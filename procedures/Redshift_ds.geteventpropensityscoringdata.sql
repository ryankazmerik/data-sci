CREATE OR REPLACE PROCEDURE ds.geteventpropensityscoringdata(in _lkupclientid int4, in event_date date, inout rs_out refcursor)
	LANGUAGE plpgsql
AS $$
	
	
	
	
	
	
		

DECLARE
    days_out int := datediff(day, current_date, event_date);
BEGIN

    SET enable_case_sensitive_identifier TO true;
	SET enable_result_cache_for_session TO false;

    drop table if exists daysout2;
    drop table if exists event_attributes2;
    drop table if exists events2;
    drop table if exists customerPurchase2;
    drop table if exists customer2;
    drop table if exists customerMarketing_scoring2;
    drop table if exists customerEventTmp2;
    drop table if exists customerPurchase_scoring2;

    -- create days out buckets
    create temp table daysout2(
        minDaysOut int, maxDaysOut int
    );
    insert into daysout2(minDaysOut, maxDaysOut) values
    (0, 1), (1, 4), (4, 8), (8, null);

    select top 1
        eventDay, team, eventTime
    into temp table event_attributes2
    from
        dw.cohortPurchase cp
    where
        lkupclientid = _lkupClientId 
        and eventDate = event_date;

    -- get prior events
    select distinct seasonYear, eventDate, eventName, team, eventDay, eventTime
    into temp table events2
    from
        dw.cohortPurchase cp
    where 
        lkupClientId = _lkupClientId
        and seasonYear <> 2020
        and productGrouping = 'Full Season'
        and eventDate < dateadd(day, -days_out, event_date);

    -- get all prior indi purchases
    select *
    into temp table customerPurchase2
    from dw.cohortPurchase p
    where p.lkupClientId = _lkupClientId 
        and p.productType = 'Individual'
        -- potentially remove
        and secondaryAction is null
        and eventDate < dateadd(day, -days_out, event_date);

    -- customer attributes
    select
        c.dimCustomerMasterId,
        c.inMarket,
        c.distanceToVenue,
        min(p.purchaseDate) as minPurchaseDate
    into temp table customer2
    from dw.cohortCustomer c
        join customerPurchase2 p on c.dimCustomerMasterId = p.dimCustomerMasterId
    where
        c.accountType not in ('Broker', 'Employee')
        -- and c.dimCustomerMasterId = 2179936
    group by c.dimCustomerMasterId, c.inMarket, c.distanceToVenue;

    -- recent marketing attributes
    select 
        m.dimCustomerMasterId,
        cast(sum(m.numOpens) as float) / case when sum(m.numSends) = 0 then 1 else sum(m.numSends) end as recent_openRate,
        cast(sum(m.numClicks) as float) / case when sum(m.numOpens) = 0 then 1 else sum(m.numOpens) end as recent_clickRate
    into temp table customerMarketing_scoring2
    from dw.cohortMarketing m
        join customer2 c on m.dimCustomerMasterId = c.dimCustomerMasterId
    where m.lkupClientId = _lkupClientId
        and m.activityDate between dateadd(day, -15, event_date) and dateadd(day, -8, event_date)  -- week out from minDay
    group by m.dimCustomerMasterId;

    -- get past event/purchase data to calculate frequencies for target event. Only get data for customers that have made a purchase before (not first purchase)
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
    into temp table customerEventTmp2
    from events2 e
        join customerPurchase2 p on p.eventName = e.eventName
        join customer2 c on p.dimCustomerMasterId = c.dimCustomerMasterId
    where p.lkupClientId = _lkupClientId
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
        ce.dimCustomerMasterId,
        cast(sum(ce.did_purchase) as float) events_purchased,
        cast(sum(case when ce.team = ea.team then ce.did_purchase end) as float) / sum(case when ce.team = ea.team then 1 end) frequency_opponent,
        cast(sum(case when ce.eventDay = ea.eventDay then ce.did_purchase end) as float) / sum(case when ce.eventDay = ea.eventDay then 1 end) frequency_eventDay,
        cast(sum(case when ce.eventTime = ea.eventTime then ce.did_purchase end) as float) / sum(case when ce.eventTime = ea.eventTime then 1 end) frequency_eventTime
    into temp table customerPurchase_scoring2
    from customerEventTmp2 ce 
        cross join event_attributes2 ea
    where 1=1
    group by ce.dimCustomerMasterId;

    -- drop table datascience.yankees.event_propensity_scoring_20190330

    -- scoring data
    --drop table if exists result_set;
	--create temp table result_set as
   OPEN rs_out FOR
    select (case 
            when d.minDaysOut = 0 then 'Day Of'
            when d.minDaysOut = 1 then '1 to 3 Days Out'
            when d.minDaysOut = 4 then '4 to 7 Days Out'
            when d.minDaySOut = 8 then 'Over a Week'
        end) as "daysout",
        event_date as "eventdate",
        datediff(day, c.minPurchaseDate, event_date) - days_out as tenure,
        p.dimCustomerMasterId as "dimcustomermasterid",
        p.events_purchased,
        p.frequency_opponent,
        p.frequency_eventDay as "frequency_eventday",
        p.frequency_eventTime as "frequency_eventtime",
        c.inMarket as "inmarket",
        c.distanceToVenue as "distancetovenue",
        m.recent_openRate as "recent_openrate",
        m.recent_clickRate as "recent_clickrate"
    from customerPurchase_scoring2 p
        join customer2 c on p.dimCustomerMasterId = c.dimCustomerMasterId
        left join customerMarketing_scoring2 m on p.dimCustomerMasterId = m.dimCustomerMasterId
        cross join daysout2 d;

END;








$$
;
