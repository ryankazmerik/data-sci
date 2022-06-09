CREATE OR REPLACE PROCEDURE ds.geteventpropensitytrainingdata(_lkupclientid int4, start_year int4, end_year int4, rs_out refcursor)
	LANGUAGE plpgsql
AS $$
	
	
	
	declare 
		ratio float = 0.5;
		numPurchaseSamples int;
	    numNonPurchaseSamples int;
BEGIN

    --SET enable_case_sensitive_identifier TO true;
	SET enable_result_cache_for_session TO false;

    
	drop table if exists daysOut;
	drop table if exists #events;
	drop table if exists #customerPurchase;
	drop table if exists #customer;
	drop table if exists #customerMarketing;
	drop table if exists #customerMerch;
	drop table if exists #customerEventTmp;
	drop table if exists #customerEvent;
	drop table if exists #customerEventDaysOut;
	drop table if exists #customerEventDaysOutMarketing;
	drop table if exists #customerEventDaysOutMarketingMerch;
	drop table if exists #sample_purchases;
	drop table if exists #sample_nonPurchases;
	
    -- create days out buckets
    create temp table daysout(
        minDaysOut int, maxDaysOut int
    );
    insert into daysout(minDaysOut, maxDaysOut) values
    (0, 1), (1, 4), (4, 8), (8, null);

   
	select distinct seasonYear, eventDate, eventName, team, eventDay, eventTime
	into #events
	from dw.cohortPurchase
	where lkupClientId = _lkupclientid
	and seasonYear <> 2020
	and seasonYear < 2022
	AND CAST(seasonYear AS int) BETWEEN start_year AND end_year
	and productGrouping = 'Full Season';


	
	select *
	into #customerPurchase
	from dw.cohortPurchase p
	where p.lkupClientId = _lkupclientid 
	    and p.productType = 'Individual'
	    AND CAST(seasonYear AS int) BETWEEN start_year AND end_year
	-- filtering fucked 2022 data
	and secondaryAction is null
	and eventDate < '2022-01-01';


	
	select top 200000
	    c.dimCustomerMasterId,
	    c.inMarket,
	    c.distanceToVenue,
	    min(p.purchaseDate) as minPurchaseDate
	into #customer
	from dw.cohortCustomer c
	    join #customerPurchase p on c.dimCustomerMasterId = p.dimCustomerMasterId
	where 1=1
	    and c.accountType not in ('Broker', 'Employee')
	group by c.dimCustomerMasterId, c.inMarket, c.distanceToVenue;
	--order by newid()
	
	select m.dimCustomerMasterId, m.activityDate, sum(numSends) sends, sum(numOpens) opens, sum(numClicks) clicks
	into #customerMarketing
	from dw.cohortMarketing m
	    join #customer c on m.dimCustomerMasterId = c.dimCustomerMasterId
	where m.lkupClientId = _lkupclientid 
	group by m.dimCustomerMasterId, m.activityDate;
	
	select m.dimCustomerMasterId, min(purchaseDate) as minMerchPurchaseDate, sum(m.itemCount) itemCounts
	into #customerMerch
	from dw.cohortMerch m
	    join #customer c on m.dimCustomerMasterId = c.dimCustomerMasterId
	where m.lkupClientId = _lkupclientid 
	group by m.dimCustomerMasterId;
	
	select  
	    e.seasonYear, 
	    e.eventDate, 
	    e.eventName, 
	    e.team, 
	    e.eventDay,
	    e.eventTime,
	    p.dimCustomerMasterId, 
	    max(case when e.eventDate = p.eventDate then 1 else 0 end) as did_purchase,
	    max(case when e.eventDate = p.eventDate then p.daysOutFromEvent end) as purchasedDaysOut
	into #customerEventTmp
	from #events e, #customerPurchase p
	    join #customer c on p.dimCustomerMasterId = c.dimCustomerMasterId
	where p.lkupClientId = _lkupclientid 
	    and e.eventDate > c.minPurchaseDate
	group by 
	    e.seasonYear, 
	    e.eventDate,
	    e.eventName, 
	    e.team, 
	    e.eventDay, 
	    e.eventTime,
	    p.dimCustomerMasterId;
	
	select 
	    p.*
	    ,c.distanceToVenue
	    ,c.inMarket
	    ,(case 
	        when datediff(day, c.minPurchaseDate, p.eventDate) = p.purchasedDaysOut then 0
	        else datediff(day, c.minPurchaseDate, p.eventDate)
	    end) as tenure
	    ,count(p.eventName) over (partition by p.dimCustomerMasterId order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as events_purchased
	    ,(case 
	        when count(p.eventName) over (partition by p.dimCustomerMasterId, team order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) = 0 then 0.0
	        else cast(sum(p.did_purchase) over (partition by p.dimCustomerMasterId, team order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as float)
	            / count(p.eventName) over (partition by p.dimCustomerMasterId, team order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
	    end) frequency_opponent
	    ,(case
	        when count(p.eventName) over (partition by p.dimCustomerMasterId, eventDay order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) = 0 then 0.0
	        else cast(sum(p.did_purchase) over (partition by p.dimCustomerMasterId, eventDay order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as float)
	            / count(p.eventName) over (partition by p.dimCustomerMasterId, eventDay order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
	    end) frequency_eventDay
	    ,(case
	        when count(p.eventName) over (partition by p.dimCustomerMasterId, eventTime order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) = 0 then 0.0
	        else cast(sum(p.did_purchase) over (partition by p.dimCustomerMasterId, eventTime order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as float)
	            / count(p.eventName) over (partition by p.dimCustomerMasterId, eventTime order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
	    end) frequency_eventTime
	into #customerEvent
	from #customerEventTmp p
	    join #customer c on p.dimCustomerMasterId = c.dimCustomerMasterId
	where 1=1;
	
	-- ce x do
	
	select 
	    (case 
	        when doo.minDaysOut = 0 then 'Day Of'
	        when doo.minDaysOut = 1 then '1 to 3 Days Out'
	        when doo.minDaysOut = 4 then '4 to 7 Days Out'
	        when doo.minDaySOut = 8 then 'Over a Week'
	    end) as daysOut,
	    doo.minDaysOut,
	    doo.maxDaysOut,
	    ce.dimCustomerMasterId,
	    ce.eventDate,
	    ce.eventName,
	    ce.inMarket,
	    ce.distanceToVenue, 
	    ce.tenure,
	    ce.purchasedDaysOut,
	    (case 
	        when ce.did_purchase = 1 and ce.purchasedDaysOut >= doo.minDaysOut and ce.purchasedDaysOut < isnull(doo.maxDaysOut, ce.purchasedDaysOut + 1) then 1
	        else 0
	    end) as did_purchase,
	    ce.events_purchased,
	    ce.frequency_opponent,
	    ce.frequency_eventDay,
	    ce.frequency_eventTime
	into #customerEventDaysOut
	from #customerEvent ce, daysOut  doo
	where 1=1
	    and (ce.purchasedDaysOut is null or ce.purchasedDaysOut < isnull(doo.maxDaysOut, ce.purchasedDaysOut + 1));
	
	
	select 
	    cedo.daysOut,
	    cedo.minDaysOut,
	    cedo.maxDaysOut,
	    cedo.dimCustomerMasterId,
	    (
	        cast(sum(case when cm.activityDate <= cedo.eventDate - isnull(cedo.purchasedDaysOut, 0) then cm.clicks else 0 end) as float)
	        / case when sum(case when cm.activityDate <= cedo.eventDate - isnull(cedo.purchasedDaysOut, 0) then cm.sends else 0 end) = 0 then 1 else sum(case when cm.activityDate <= cedo.eventDate - isnull(cedo.purchasedDaysOut, 0) then cm.sends else 0 end) end 
	     )as recent_openRate,
	    (
	        cast(sum(case when cm.activityDate <= cedo.eventDate - isnull(cedo.purchasedDaysOut, 0) then cm.clicks else 0 end) as float)
	        / case when sum(case when cm.activityDate <= cedo.eventDate - isnull(cedo.purchasedDaysOut, 0) then cm.opens else 0 end) = 0 then 1 else sum(case when cm.activityDate <= cedo.eventDate - isnull(cedo.purchasedDaysOut, 0) then cm.opens else 0 end) end 
	        	     )as recent_clickRate,
	    cedo.eventDate,
	    cedo.eventName,
	    cedo.inMarket,
	    cedo.distanceToVenue,
	    cedo.tenure,
	    cedo.did_purchase,
	    cedo.events_purchased,
	    cedo.frequency_opponent,
	    cedo.frequency_eventDay,
	    cedo.frequency_eventTime
	into #customerEventDaysOutMarketing
	from #customerEventDaysOut cedo
	    left join #customerMarketing cm 
	        on cedo.dimCustomerMasterId = cm.dimCustomerMasterId
	        and datediff(day, cm.activityDate, cedo.eventDate) between minDaysOut and minDaysOut + 7 -- week out from minDay
	where 1=1
	group by
	    cedo.daysOut,
	    cedo.minDaysOut,
	    cedo.maxDaysOut,
	    cedo.dimCustomerMasterId,
	    cedo.eventDate,
	    cedo.eventName,
	    cedo.inMarket,
	    cedo.distanceToVenue,
	    cedo.tenure,
	    cedo.did_purchase,
	    cedo.events_purchased,
	    cedo.frequency_opponent,
	    cedo.frequency_eventDay,
	    cedo.frequency_eventTime
	order by eventDate desc, daysOut desc;
	
	select 
	    cedom.daysOut,
	    cedom.minDaysOut,
	    cedom.maxDaysOut,
	    cedom.dimCustomerMasterId,
	    cedom.recent_openRate,
	    cedom.recent_clickRate,
	    cedom.eventDate,
	    cedom.eventName,
	    cedom.inMarket,
	    cedom.distanceToVenue,
	    cedom.tenure,
	    cedom.did_purchase,
	    cedom.events_purchased,
	    cedom.frequency_opponent,
	    cedom.frequency_eventDay,
	    cedom.frequency_eventTime,
	    isnull(cm.itemCounts, 0) count_merchOwned
	into #customerEventDaysOutMarketingMerch
	from #customerEventDaysOutMarketing cedom
	    left join #customerMerch cm
	        on cedom.dimCustomerMasterId = cm.dimCustomerMasterId
	        and cm.minMerchPurchaseDate < cedom.eventDate - minDaysOut
	where 1=1
	order by dimCustomerMasterId, eventDate asc;
	
	   
	-- scoring data
	select *
	into #sample_purchases
	from #customerEventDaysOutMarketingMerch where did_purchase = 1 and tenure <> 0;
	
	numPurchaseSamples = (select count(*) from #sample_purchases);
    numNonPurchaseSamples = ratio * numPurchaseSamples / (1 - ratio);

   	raise notice 'numPurchaseSamples, %', numPurchaseSamples;
   	raise notice 'numNonPurchaseSamples, %', numNonPurchaseSamples;

   
	drop table if exists #sample_nonPurchases;
 	execute 'create temp table #sample_nonPurchases as 
   	select top ' || numNonPurchaseSamples || ' *
	from #customerEventDaysOutMarketingMerch
	where did_purchase = 0';

	OPEN rs_out FOR
	
	select * 
	from (
	    select * from #sample_purchases
	    union
	    select * from #sample_nonPurchases
	) as tmp;

   
END;



$$
;
