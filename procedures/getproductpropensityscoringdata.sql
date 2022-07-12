CREATE OR REPLACE PROCEDURE ds.getproductpropensityscoringdata(_lkupclientid int4, min_date date, max_date date, rs_out refcursor)
	LANGUAGE plpgsql
AS $$
	
	
	
	
	
	
	
	
	
	
	
	
	
	-- find year to begin training data from
	declare 
		season_min_train INT := (select min(cp.seasonYear) from dw.cohortPurchase cp where cp.lkupClientId = _lkupClientId);
		max_product_order int = (select max(d.displayorder) from dw.dimproduct d where d.lkupclientid = _lkupClientId);
        _clientcode varchar(20) = (select top 1 clientcode from dw.tenantconfig t where t.lkupclientid = _lkupClientId);

BEGIN
	
	drop table if exists #seasons;
	drop table if exists #customers;
	drop table if exists #eventsByCustomer;
	drop table if exists #customersSeasons;
	drop table if exists #seasonsByCustomer;
	
	-- find list of season years to aggregate data for
	drop table if exists #seasons;
	select distinct seasonYear 
	into #seasons
	from dw.cohortPurchase cp
	where cast(cp.eventdate as date) between min_date and max_date -1
	and cp.lkupclientid = _lkupClientId;

	drop table if exists #customers;
	select
		cc.dimCustomerMasterId,
		max(NVL(cc.distanceToVenue, 0)) as distance
	into #customers
	from dw.cohortCustomer cc
		join dw.cohortPurchase cp on cc.dimCustomerMasterId = cp.dimCustomerMasterId
	where
		cc.lkupClientId = _lkupClientId
		and cast(cp.eventdate as date) between min_date and max_date -1
		and cp.productGrouping not like '%group%'
		and (
			cc.accountType is null or
			cc.accountType not in ('Staff', 'Broker', 'Sponsor'))
	group by
		cc.dimCustomerMasterId
	order by
		cc.dimCustomerMasterId;
	
	
	update #customers
	set
		distance = (select avg(distance) from #customers)
	where
		distance = 0;
	
	
	drop table if exists #eventsByCustomer;
	select
		c.dimCustomerMasterId,
		max(c.distance) as distance,
		cp.seasonYear,
		cp.eventDate,
		max(case when cp.attendanceCount > 0 then 1 else 0 end) attended,
		sum(cp.ticketCount) as volume,
		sum(cp.revenue) as spend
	into #eventsByCustomer
	from #customers c
		join dw.cohortPurchase cp on c.dimCustomerMasterId = cp.dimCustomerMasterId
	where
		cp.lkupClientId = _lkupClientId
		and cast(cp.eventdate as date) between min_date and max_date -1
		and cp.productGrouping not like '%group%'
	group by
		c.dimCustomerMasterId,
		cp.seasonYear,
		cp.eventDate
	order by
		c.dimCustomerMasterId,
		cp.seasonYear;
	
	
	-- unique customer list
	drop table if exists #customersSeasons;
	select
		c.dimCustomerMasterId,
		c.distance,
		s.seasonYear
	into #customersSeasons
	from #customers c, #seasons s
	order by
		c.dimCustomerMasterId,
		s.seasonYear;
	
	-- all migration products
	drop table if exists #products;
	SELECT DISTINCT
	productgrouping,
	displayorder
	into #products
	from dw.dimproduct dp
	WHERE dp.lkupClientId = _lkupClientId
	and displayorder is not null
	order by displayorder, productgrouping;

	insert into #products (productgrouping, displayorder)
	values ('Individual', (max_product_order + 1));


	drop table if exists #customer_prod_migr;
	select 
		cp.seasonYear as Year,
		cp.dimCustomerMasterId,
		cp.productgrouping as Product,
		p.displayOrder as ProductRank,
		COUNT(DISTINCT cp.eventname) AS numOfEvents,
		SUM(cp.ticketCount) AS purchaseCount,
		SUM(cp.ticketCount) AS totalVolume,
		SUM(cp.revenue) AS totalRevenue
	into #customer_prod_migr
	from #products p
		left join dw.cohortpurchase cp
		on p.productgrouping = cp.productgrouping
	where 
		cp.lkupclientid = _lkupClientId
		and cp.secondaryaction is null
		and cast(cp.eventdate as date) between min_date and max_date -365
		and cp.dimcustomermasterid > 0
	group by
		cp.lkupclientid,
		cp.seasonYear,
		cp.dimCustomerMasterId,
		cp.productgrouping,
		p.displayOrder;
	
	insert into #customer_prod_migr
	select 
		cp.seasonYear as Year,
		cp.dimCustomerMasterId,
		'Individual' as Product,
		(max_product_order + 1) as ProductRank,
		COUNT(DISTINCT cp.eventname) AS numOfEvents,
		SUM(cp.ticketCount) AS purchaseCount,
		SUM(cp.ticketCount) AS totalVolume,
		SUM(cp.revenue) AS totalRevenue
	from dw.cohortpurchase cp  
	where 
		cp.lkupclientid = _lkupClientId 
		and cp.secondaryaction is null
		and cp.productType = 'Individual'
		and cp.dimcustomermasterid > 0
		and cp.isregularseason = 1
		and cast(cp.eventdate as date) between min_date and max_date -365
	group by
		cp.lkupclientid,
		cp.seasonYear,
		cp.dimCustomerMasterId;
	
	
	drop table if exists #customer_products;
	select distinct 
		year, dimCustomerMasterId, product, productRank, numOfEvents, purchaseCount, totalVolume, totalRevenue
	into #customer_products
	from
		(
		SELECT
			Year,
			dimCustomerMasterId,
			Product,
			ProductRank,
			MIN(ProductRank) OVER (PARTITION BY dimCustomerMasterId, Year) AS MinProductRank,
			numOfEvents, 
			purchaseCount,
			totalVolume,
			totalRevenue
		from
			#customer_prod_migr
		) a
		WHERE ProductRank = MinProductRank;
	
	
	-- get total events and attendance count by season per customer
	drop table if exists #seasonsByCustomer;
	select
		cs.dimCustomerMasterId,
		max(cs.distance) as distance,
		cs.seasonYear,
		count(ebc.eventDate) as events,
		sum(case
			when ebc.attended is null then 0
			else ebc.attended
		end) as attended,
		case
			when sum(ebc.volume) = 0 or sum(ebc.spend)/sum(ebc.volume) is null then 0
			else sum(ebc.spend)/sum(ebc.volume)
		end as atp,
		max(case
			when cp.product is null or cp.product like '%group%' then 'None'
			else cp.product
		end) as product
	into #seasonsByCustomer
	from #customersSeasons cs
		left join #eventsByCustomer ebc
			on cs.dimCustomerMasterId = ebc.dimCustomerMasterId
			and cs.seasonYear = ebc.seasonYear
		left join #customer_products cp
			on cs.dimCustomerMasterId = cp.dimCustomerMasterId
			and cs.seasonYear = cp.year
	group by
		cs.dimCustomerMasterId,
		cs.seasonYear
	order by
		cs.dimCustomerMasterId,
		cs.seasonYear;
	

	-- final select for customer attributes
	--drop table if exists result_set;
	--create temp table result_set as 
	OPEN rs_out FOR
	select
    	_lkupclientid as lkupclientid,
        _clientcode as clientcode,
		sbc_now.dimCustomerMasterId,
		round(max(sbc_now.distance),2)  as distance,
		sbc_now.seasonYear,
		sum(case
			when sbc_past.seasonYear < sbc_now.seasonYear then sbc_past.events
			else 0
		end) as events_prior,
		sum(case
			when sbc_past.seasonYear < sbc_now.seasonYear then sbc_past.attended
			else 0
		end) as attended_prior,
		sum(case
			when ((sbc_past.seasonYear = sbc_now.seasonYear - 1) or (sbc_past.seasonYear = 2019 and sbc_now.seasonYear = 2021)) then sbc_past.events
			else 0
		end) as events_last,
		sum(case
			when ((sbc_past.seasonYear = sbc_now.seasonYear - 1) or (sbc_past.seasonYear = 2019 and sbc_now.seasonYear = 2021)) then sbc_past.attended
			else 0
		end) as attended_last,
		cast(sbc_now.seasonYear as int) - min(cast(case
			when sbc_past.events > 0 then sbc_past.seasonYear
			else sbc_now.seasonYear
		end as int)) - 1 as tenure,
		round(max(case
			when ((sbc_past.seasonYear = sbc_now.seasonYear - 1) or (sbc_past.seasonYear = 2019 and sbc_now.seasonYear = 2021)) then sbc_past.atp
			else 0
		end),2)  as atp_last,
		max(sbc_now.product) as product_current,
        max(case
			when ((sbc_past.seasonYear = sbc_now.seasonYear - 1) or (sbc_past.seasonYear = 2019 and sbc_now.seasonYear = 2021)) then sbc_past.product
		end) as product_last
	from #seasonsByCustomer sbc_now
		join #seasonsByCustomer sbc_past
			on sbc_now.dimCustomerMasterId = sbc_past.dimCustomerMasterId
	--where sbc_now.seasonYear between season_min_train and season_max -1
	group by
		sbc_now.dimCustomerMasterId,
		sbc_now.seasonYear
	
	order by
		sbc_now.dimCustomerMasterId asc,
		sbc_now.seasonYear asc;

	
END;












$$
;
