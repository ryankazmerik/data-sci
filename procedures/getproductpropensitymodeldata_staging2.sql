use [mlsInterMiami]
go


declare @season_min_data int = 2020;
declare @season_max int = 2023;

drop table if exists #events;
drop table if exists #seasons;
drop table if exists #products;
drop table if exists #tickets;
drop table if exists #customers;
drop table if exists #eventsByCustomer;
drop table if exists #customersSeasons;
drop table if exists #seasonsByCustomer;
drop table if exists #customer_prod_migr;
drop table if exists #comp_holders


select e.*
into #events
from staging2.event e
    join staging2.etlControlRecord ecr 
        on e.sourceEventId = ecr.controlKey
        and ecr.controlProcess = 'event'
        and controlIsActive = 1

declare @season_min_train int = (
    select min(s.seasonYear) 
    from #events e
        join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
);
declare @season int = @season_min_train;
declare @max_product_order int = (select max(displayOrder) from staging2.product);

-- find list of season years to aggregate data for
select distinct s.seasonYear 
into #seasons
from #events e
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
-- where s.seasonYear <> 2020; -- ignore covid

select 
    scv.dimCustomerMasterId,
    t.*,
    (case when a.acctId is null then 1 else 0 end) as attended,
    p.productGrouping,
    p.displayOrder,
    e.eventDate,
    e.eventName,
    e.sourceEventId,
    s.sourceSeasonId,
    s.seasonYear,
    s.seasonName
into #tickets
from staging2.ticketHistory t
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
    join staging2.product p on p.productGrouping = t.productDescription
    left join staging2.attendance a 
        on a.eventId = t.eventId
        and a.sectionName = t.sectionName
        and a.rowName = t.rowName
        and a.seatNum = t.seatNum
    join scv.customerMasterDetail scv 
        on t.customerNumber = scv.sourceCustomerId
        and scv.sourceSystemGroup = 'Ticketing'
    join scv.dimCustomerMaster dcm
        on scv.dimCustomerMasterId = dcm.dimCustomerMasterId
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1

select
    dcm.dimCustomerMasterId,
    max(isnull(dcm.distanceToVenue, 0)) as distance
into #customers
from #tickets t
    join scv.dimCustomerMaster dcm
        on t.dimCustomerMasterId = dcm.dimCustomerMasterId
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    and t.seasonYear between @season_min_data and @season_max
    and t.productGrouping not like '%group%'
    and (
        dcm.accountType is null or
        dcm.accountType not in ('Staff', 'Broker', 'Sponsor')
    )
group by
    dcm.dimCustomerMasterId
order by
    dcm.dimCustomerMasterId;

update #customers
set distance = (select avg(distance) from #customers)
where distance = 0;

select
    c.dimCustomerMasterId,
    max(c.distance) as distance,
    t.seasonYear,
    t.eventDate,
    max(t.attended) attended,
    count(t.seatNum) as volume,
    sum(t.reportedRev) as spend
into #eventsByCustomer
from #tickets t
    join #customers c 
        on t.dimCustomerMasterId = c.dimCustomerMasterId
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    and cast(t.seasonYear as int) between @season_min_data and @season_max
    and t.productGrouping not like '%group%'
group by
    c.dimCustomerMasterId,
    t.seasonYear,
    t.eventDate
order by
    c.dimCustomerMasterId,
    t.seasonYear;

-- unique customer list
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
SELECT DISTINCT
    productgrouping,
    displayorder
into #products
from staging2.product dp
WHERE displayorder is not null
order by displayorder, productgrouping;

insert into #products (productgrouping, displayorder)
values ('Individual', (@max_product_order + 1));

select 
    t.seasonYear as Year,
    t.dimCustomerMasterId,
    t.productgrouping as Product,
    p.displayOrder as ProductRank,
    COUNT(DISTINCT t.eventname) AS numOfEvents,
    COUNT(t.seatNum) AS purchaseCount,
    COUNT(t.seatNum) AS totalVolume,
    SUM(t.reportedRev) AS totalRevenue
into #customer_prod_migr
from #products p
    left join #tickets t
        on p.productgrouping = t.productgrouping
where t.seasonYear between @season_min_data and @season_max - 1
    and t.dimcustomermasterid > 0
group by
    t.seasonYear,
    t.dimCustomerMasterId,
    t.productgrouping,
    p.displayOrder;

insert into #customer_prod_migr
select 
    t.seasonYear as Year,
    t.dimCustomerMasterId,
    'Individual' as Product,
    (@max_product_order + 1) as ProductRank,
    COUNT(DISTINCT t.eventname) AS numOfEvents,
    COUNT(t.seatNum) AS purchaseCount,
    COUNT(t.seatNum) AS totalVolume,
    SUM(t.reportedRev) AS totalRevenue
from #tickets t  
where t.productGrouping = 'Individual'
    and t.dimcustomermasterid > 0
    and t.seasonYear between @season_min_data and @season_max - 1
group by
    t.seasonYear,
    t.dimCustomerMasterId;

drop table if exists #customer_products;
select distinct 
    year, dimCustomerMasterId, product, productRank, numOfEvents, purchaseCount, totalVolume, totalRevenue
into #customer_products
from (
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


-- exclude comp ticket holders for last season
select distinct dimCustomerMasterId
into #comp_holders
from #tickets t
    join staging2.product p on t.productGrouping = p.productGrouping
where seasonYear = @season_max - 1
and p.IsComp = 1;

select
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
    left join #comp_holders c 
        on sbc_now.dimCustomerMasterId = c.dimCustomerMasterId
where sbc_now.seasonYear between @season_min_train and @season_max
    and c.dimCustomerMasterId is null
group by
    sbc_now.dimCustomerMasterId,
    sbc_now.seasonYear
having
    max(case
        when ((sbc_past.seasonYear = sbc_now.seasonYear - 1) or (sbc_past.seasonYear = 2019 and sbc_now.seasonYear = 2021)) then sbc_past.product
    end) is not null
    and (cast(sbc_now.seasonYear as int) - min(cast(case
        when sbc_past.events > 0 then sbc_past.seasonYear
        else sbc_now.seasonYear
    end as int)) - 1) > -1
order by
    sbc_now.dimCustomerMasterId asc,
    sbc_now.seasonYear asc;
