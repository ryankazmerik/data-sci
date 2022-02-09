use stlrYankees
go

/*
do
- buckets

e
- events

c
- sample customers

cp x c
- purchase data

cm x c
- marketing data

cp x e
- lifetime events purchased
- lifetime opponents bought
- lifetime event day
- tenure

ce x do
- did_purchase
- ratio logic

cm x cedo
- open rate between days out
- click rate between days out
*/

drop table if exists #daysOut
select minDaysOut, maxDaysOut 
into #daysOut
from (values (0, 1), (1, 4), (4, 8), (8, null)) 
as tmp(minDaysOut, maxDaysOut);

drop table if exists #events;
select distinct seasonYear, eventDate, eventName, team, eventDay, eventTime
into #events
from dw.cohortPurchase
where lkupClientId = 53
and seasonYear <> 2020
and seasonYear < 2022
and productGrouping = 'Full Season'

drop table if exists #customerPurchase
select *
into #customerPurchase
from dw.cohortPurchase p
where p.lkupClientId = 53
    and p.productType = 'Individual'
-- filtering fucked 2022 data
and secondaryAction is null
and eventDate < '2022-01-01'

drop table if exists #customer
select top 100000
    c.dimCustomerMasterId,
    c.inMarket,
    c.distanceToVenue,
    min(p.purchaseDate) as minPurchaseDate
into #customer
from dw.cohortCustomer c
    join #customerPurchase p on c.dimCustomerMasterId = p.dimCustomerMasterId
where 1=1
    -- debug
    -- and p.dimCustomerMasterId = 24853291
    -- and p.dimCustomerMasterId = 745312
group by c.dimCustomerMasterId, c.inMarket, c.distanceToVenue
order by newid()

-- drop table if exists #customerMarketing
-- select m.dimCustomerMasterId, m.activityDate, sum(numSends) sends, sum(numOpens) opens, sum(numClicks) clicks
-- into #customerMarketing
-- from dw.cohortMarketing m
--     join #customer c on m.dimCustomerMasterId = c.dimCustomerMasterId
-- where m.lkupClientId = 53 
-- group by m.dimCustomerMasterId, m.activityDate
-- option (maxdop 0) 

-- c x e
drop table if exists #customerEventTmp;
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
where p.lkupClientId = 53 
    and e.eventDate > c.minPurchaseDate
group by 
    e.seasonYear, 
    e.eventDate,
    e.eventName, 
    e.team, 
    e.eventDay, 
    e.eventTime,
    p.dimCustomerMasterId

drop table if exists #customerEvent;
select 
    p.*
    ,c.distanceToVenue
    ,c.inMarket
    ,(case 
        when datediff(day, c.minPurchaseDate, p.eventDate) = p.purchasedDaysOut then 0
        else datediff(day, c.minPurchaseDate, p.eventDate)
    end) as tenure
    ,(case 
        when count(p.eventName) over (partition by p.dimCustomerMasterId order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) = 0 then 0.0
        else cast(sum(p.did_purchase) over (partition by p.dimCustomerMasterId order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as float)
            / count(p.eventName) over (partition by p.dimCustomerMasterId order by p.eventDate asc ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
    end) events_purchased
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
where 1=1

-- ce x do

drop table if exists #customerEventDaysOut
select 
    do.minDaysOut,
    do.maxDaysOut,
    ce.dimCustomerMasterId,
    ce.eventDate,
    ce.eventName,
    -- ce.eventDay,
    -- ce.eventTime,
    ce.inMarket,
    ce.distanceToVenue,
    ce.tenure,
    (case 
        when ce.did_purchase = 1 and ce.purchasedDaysOut >= do.minDaysOut and ce.purchasedDaysOut < isnull(do.maxDaysOut, ce.purchasedDaysOut + 1) then 1
        else 0
    end) as did_purchase,
    ce.events_purchased,
    ce.frequency_opponent,
    ce.frequency_eventDay,
    ce.frequency_eventTime
into #customerEventDaysOut
from #customerEvent ce, #daysOut do 
where 1=1
    and (ce.purchasedDaysOut is null or ce.purchasedDaysOut < isnull(do.maxDaysOut, ce.purchasedDaysOut + 1))


-- scoring data
drop table if exists #sample_purchases
select *
into #sample_purchases
from #customerEventDaysOut where did_purchase = 1

declare @ratio float = 0.5
declare @numPurchaseSamples int = (select count(*) from #sample_purchases)
declare @numNonPurchaseSamples int = @ratio * @numPurchaseSamples / (1 - @ratio)


select top(@numNonPurchaseSamples) *
into #sample_nonPurchases
from #customerEventDaysOut
where did_purchase = 0
order by newid()

select * from #sample_purchases
union
select * from #sample_nonPurchases
