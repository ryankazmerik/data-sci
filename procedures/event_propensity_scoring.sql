use stlrYankees
go

/*
1. pick 3 2019 events (early, mid, mate)
2. pull everyone who purchased prior to those events
3. lead list was pulled at least a week out

@event, @daysOut 
- weeks out will include all 4 buckets

- post scoring
- rank on highest score and take top 20k
- for the given event compare conversion rate to the entire popo

*/

set transaction isolation level read uncommitted;

declare @eventDate datetime = '2019-03-30'
-- declare @eventDate datetime = '2019-07-12'
-- declare @eventDate datetime = '2019-09-17'
declare @daysOut int = 8

drop table if exists #daysOut
drop table if exists #events
drop table if exists #customerPurchase
drop table if exists #customer
drop table if exists #customerMarketing_scoring
drop table if exists #customerEventTmp
drop table if exists #customerPurchase_scoring

select minDaysOut, maxDaysOut 
into #daysOut
from (values (0, 1), (1, 4), (4, 8), (8, null)) 
as tmp(minDaysOut, maxDaysOut);

select distinct seasonYear, eventDate, eventName, team, eventDay, eventTime
into #events
from dw.cohortPurchase
where lkupClientId = 53
and seasonYear <> 2020
and productGrouping = 'Full Season'
and eventDate < dateadd(day, -@daysOut, @eventDate)

select *
into #customerPurchase
from dw.cohortPurchase p
where p.lkupClientId = 53 
    and p.productType = 'Individual'
-- filtering fucked 2022 data
and secondaryAction is null
and eventDate < dateadd(day, -@daysOut, @eventDate)

select
    c.dimCustomerMasterId,
    c.inMarket,
    c.distanceToVenue,
    min(p.purchaseDate) as minPurchaseDate
into #customer
from dw.cohortCustomer c
    join #customerPurchase p on c.dimCustomerMasterId = p.dimCustomerMasterId
where 1=1
    and c.accountType not in ('Broker', 'Employee')
    -- and c.dimCustomerMasterId = 2179936
group by c.dimCustomerMasterId, c.inMarket, c.distanceToVenue

select 
    m.dimCustomerMasterId,
    cast(sum(m.numOpens) as float) / iif(sum(m.numSends) = 0, 1, sum(m.numSends)) as recent_openRate,
    cast(sum(m.numClicks) as float) / iif(sum(m.numOpens) = 0, 1, sum(m.numOpens)) as recent_clickRate
into #customerMarketing_scoring
from dw.cohortMarketing m
    join #customer c on m.dimCustomerMasterId = c.dimCustomerMasterId
where m.lkupClientId = 53
    and m.activityDate between dateadd(day, -15, @eventDate) and dateadd(day, -8, @eventDate)  -- week out from minDay
group by m.dimCustomerMasterId

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

select 
    ce.dimCustomerMasterId,
    cast(sum(ce.did_purchase) as float) events_purchased,
    cast(sum(case when ce.team = 'Baltimore Orioles' then ce.did_purchase end) as float) / sum(case when ce.team = 'Baltimore Orioles' then 1 end) frequency_opponent,
    cast(sum(case when ce.eventDay = 'SAT' then ce.did_purchase end) as float) / sum(case when ce.eventDay = 'SAT' then 1 end) frequency_eventDay,
    cast(sum(case when ce.eventTime = 'Afternoon' then ce.did_purchase end) as float) / sum(case when ce.eventTime = 'Afternoon' then 1 end) frequency_eventTime
into #customerPurchase_scoring
from #customerEventTmp ce 
where 1=1
group by ce.dimCustomerMasterId

-- drop table datascience.yankees.event_propensity_scoring_20190330

-- scoring data
select (case 
        when do.minDaysOut = 0 then 'Day Of'
        when do.minDaysOut = 1 then '1 to 3 Days Out'
        when do.minDaysOut = 4 then '4 to 7 Days Out'
        when do.minDaySOut = 8 then 'Over a Week'
    end) as daysOut,
    @eventDate as eventDate,
    datediff(day, c.minPurchaseDate, @eventDate) - @daysOut as tenure,
    p.dimCustomerMasterId,
    p.events_purchased,
    p.frequency_opponent,
    p.frequency_eventDay,
    p.frequency_eventTime,
    c.inMarket,
    c.distanceToVenue,
    m.recent_openRate,
    m.recent_clickRate
into datascience.yankees.event_propensity_scoring_20190330
from #customerPurchase_scoring p
    join #customer c on p.dimCustomerMasterId = c.dimCustomerMasterId
    left join #customerMarketing_scoring m on p.dimCustomerMasterId = m.dimCustomerMasterId
    cross join #daysOut do

-- weeks out will include all 4 buckets

select top 100 
    [s].[daysOut],
    [s].[eventDate],
    [s].[tenure],
    [s].[dimCustomerMasterId],
    [s].[events_purchased],
    [s].[frequency_opponent],
    [s].[frequency_eventDay],
    [s].[frequency_eventTime],
    [s].[inMarket],
    [s].[distanceToVenue],
    [s].[recent_openRate],
    [s].[recent_clickRate]
from DataScience.yankees.event_propensity_scoring_20190330 s

-- select count(distinct eventDate)
-- from DataScience.yankees.event_propensity_training_noFirstPurchases2
-- where eventDate <> '2019-03-30'


-- SELECT top 100 * FROM datascience.yankees.event_propensity_training_noFirstPurchases2
drop table if exists #cl;
drop table if exists #p;

select distinct dimCustomerMasterId
into #cl
from DataScience.yankees.event_propensity_scoring_20190330 s

select distinct p.dimCustomerMasterId
into #p
from dw.cohortPurchase p
    join dw.cohortCustomer c on p.dimCustomerMasterId = c.dimCustomerMasterId
where p.productType = 'Individual'
-- filtering fucked 2022 data
and secondaryAction is null
and eventDate = '2019-03-30'

select count(b.dimCustomerMasterId), count(a.dimCustomerMasterId), cast(count(b.dimCustomerMasterId) as float) /count(a.dimCustomerMasterId)
from #cl a
    left join #p b on a.dimCustomerMasterId = b.dimCustomerMasterId


select marketableState, sum(purchased) as purchasers, count(*) as leads, cast(sum(purchased) as float) / count(*) as conv, min(score) minScore, max(score) maxScore
from (
    select c.marketableState, a.id, score, (case when p.dimCustomerMasterId is null then 0 else 1 end) purchased
    from DataScience.yankees.yankees_20190330_scores a
        join dw.cohortCustomer c on c.dimCustomerMasterId = a.id
        left join #p p on a.id = p.dimCustomerMasterId
    -- order by score desc, purchased desc
) as tmp
group by marketableState


/*
Full Lead List
896	412191	0.002173749548146369	0.0134	1
278	20000	0.0139	0.7861	1

RU Leads
896	69952	0.012808783165599268	0.0134	1
519	20000	0.02595	0.5947	1
396	10000	0.0396	0.6956	1
247	5000	0.0494	0.808	1

*/