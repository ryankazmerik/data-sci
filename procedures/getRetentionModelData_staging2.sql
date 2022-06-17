use [mlsInterMiami]
go

declare @start_year int = 2019
declare @end_year int = 2022

drop table if exists #events;
drop table if exists #maxEventDate;
drop table if exists #customerMinDates;
drop table if exists #totalGames;
drop table if exists #recency;
drop table if exists #attendance;
drop table if exists #purchase;
drop table if exists #customerData;
drop table if exists #customers;
drop table if exists #consecGamesMissedTbl;
drop table if exists #customerBuckets;
drop table if exists #missedStreak;
drop table if exists #missedStreakFinal;
drop table if exists #customerBucketDetails;
drop table if exists #missed_games_data;
drop table if exists #primaryTicketScoringDataTemp;
drop table if exists #primaryTicketScoringData;
drop table if exists #secondaryTicketData;
drop table if exists #customerSeasonProductAgg;
drop table if exists #nextyearbuyer;

select e.*
into #events
from staging2.event e
    join staging2.etlControlRecord ecr 
        on e.sourceEventId = ecr.controlKey
        and ecr.controlProcess = 'event'
        and controlIsActive = 1

-- max events with attendance
select s.seasonYear, max(e.eventDate) maxEventDate
into #maxEventDate
from [staging2].[ticketHistory] t
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
    join staging2.product p on p.productGrouping = t.productDescription
    left join staging2.attendance a 
        on a.eventId = t.eventId
        and a.sectionName = t.sectionName
        and a.rowName = t.rowName
        and a.seatNum = t.seatNum
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    -- and s.isRegularSeason = 1 -- not set yet
    and e.eventDate < getdate()
    and p.isPlanProduct = 1
    and s.seasonYear BETWEEN @start_year AND @end_year
group by s.seasonYear
having count(a.ticketAcctId) > 0;

-- first purchase date by customer
select scv.dimCustomerMasterId, min(t.startDate) as minDate
into #customerMinDates
from staging2.ticketHistory t
    join scv.customerMasterDetail scv 
        on t.customerNumber = scv.sourceCustomerId
        and scv.sourceSystemGroup = 'Ticketing'
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    -- and s.isRegularSeason = 1 -- not set yet
    and s.seasonYear BETWEEN @start_year AND @end_year
group by scv.dimCustomerMasterId;

-- total attended games by customer, season and product
select scv.dimCustomerMasterId , s.seasonYear, p.productGrouping, count(distinct e.eventName) as totalGames
into #totalGames
from staging2.ticketHistory t
    join scv.customerMasterDetail scv 
        on t.customerNumber = scv.sourceCustomerId
        and scv.sourceSystemGroup = 'Ticketing'
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
    join staging2.product p on t.productDescription = p.productGrouping
    left join staging2.attendance a
        on a.eventId = t.eventId
        and a.sectionName = t.sectionName
        and a.rowName = t.rowName
        and a.seatNum = t.seatNum
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    and p.isPlanProduct = 1
    and a.ticketAcctId is not null -- utilized
    and s.seasonYear BETWEEN @start_year AND @end_year
group by scv.dimCustomerMasterId, s.seasonYear, p.productGrouping
order by totalGames desc

-- recency info by customer, season and product
select 
    dimCustomerMasterId, 
    seasonYear,
    productGrouping,
    row_number() over (partition by dimCustomerMasterId, seasonYear, productGrouping order by eventDate asc) as rowNum,
    attended
into #recency
from (
    select 
        scv.dimCustomerMasterId,
        s.seasonYear,
        p.productGrouping,
        e.eventDate,
        max(case when a.ticketAcctId is null then 0 else 1 end) as attended
    from staging2.ticketHistory t
        join scv.customerMasterDetail scv 
            on t.customerNumber = scv.sourceCustomerId
            and scv.sourceSystemGroup = 'Ticketing'
        join #events e on t.eventId = e.sourceEventId
        join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
        join staging2.product p on t.productDescription = p.productGrouping
        join #maxEventDate maxE on s.seasonYear = maxE.seasonYear
        left join staging2.attendance a
            on a.eventId = t.eventId
            and a.sectionName = t.sectionName
            and a.rowName = t.rowName
            and a.seatNum = t.seatNum 
    where t.transactionType = 'PRIMARY SALE'
        and t.isActive = 1
        and t.reportedRev > 0
        -- and s.isRegularSeason = 1
        and p.isPlanProduct = 1
        and e.eventDate < maxE.maxEventDate
    group by scv.dimCustomerMasterId, s.seasonYear, p.productGrouping, e.eventDate
) a;

SELECT
    dimCustomerMasterId,
    seasonYear,
    productGrouping,
    MAX(rowNum) AS attended
INTO #attendance
FROM #recency
WHERE attended = 1
GROUP BY
    dimCustomerMasterId,
    seasonYear,
    productGrouping;

-- latest purchased event
SELECT
    dimCustomerMasterId,
    seasonYear,
    productGrouping,
    MAX(rowNum) AS bought
INTO #purchase
FROM #recency
GROUP BY
    dimCustomerMasterId,
    seasonYear,
    productGrouping;


-- Missed games customer data
select 
    s.seasonYear,
    scv.dimCustomerMasterId,
    p.productGrouping,
    e.eventDate,
    case when count(a.ticketAcctId) > 0 then 1 else 0 end as attendanceCount,
    case when count(a.ticketAcctId) > 0 then 0 else 1 end  as missedCount
into #customerData
from staging2.ticketHistory t
    join scv.customerMasterDetail scv 
        on t.customerNumber = scv.sourceCustomerId
        and scv.sourceSystemGroup = 'Ticketing'
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
    join staging2.product p on t.productDescription = p.productGrouping
    join #maxEventDate maxE on s.seasonYear = maxE.seasonYear
    left join staging2.attendance a
        on a.eventId = t.eventId
        and a.sectionName = t.sectionName
        and a.rowName = t.rowName
        and a.seatNum = t.seatNum 
where t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    -- and s.isRegularSeason = 1 -- not set yet
    and p.isPlanProduct = 1
    AND CAST(s.seasonYear AS int) BETWEEN @start_year AND @end_year
    AND e.eventDate < maxE.maxEventDate
group by 
    s.seasonYear,
    scv.dimCustomerMasterId,
    p.productGrouping,
    e.eventDate

--  distinct customers per season per product from missed games data
SELECT DISTINCT 
    seasonYear,
    productGrouping,
    dimCustomerMasterId
INTO #customers
FROM #customerData;

-- get consecutive games missed
SELECT 
    consecGamesMissed, 
    sortOrder
INTO #consecGamesMissedTbl
FROM (
    SELECT '1' consecGamesMissed, 1 sortOrder
    UNION ALL
    SELECT '2' consecGamesMissed, 2 sortOrder
    UNION ALL
    SELECT '>2' consecGamesMissed, 3 sortOrder
    ) a;

DROP TABLE IF EXISTS #customerbuckets;
SELECT 
    *
INTO #customerBuckets
FROM 
    #customers c,
    #consecGamesMissedTbl cgm;

-- partition by seasonYear, products, customer
SELECT  
    seasonYear,
    dimCustomerMasterId,
    productGrouping,
    eventDate,
    attendanceCount,
    missedCount,
    CASE WHEN missedCount = lag(missedCount,1) OVER (PARTITION BY seasonYear, productGrouping, dimCustomerMasterId ORDER BY eventDate) THEN 0 ELSE 1
    END AS changed
INTO #missedStreak
FROM
    #customerData;

SELECT  
    seasonYear,
    dimCustomerMasterId,
    productGrouping,
    attendanceCount,
    eventDate,
    missedCount,
    SUM(changed) OVER (PARTITION BY seasonYear, productGrouping, dimCustomerMasterId ORDER BY eventDate rows between unbounded preceding and current row) grp
INTO #missedStreakFinal
FROM #missedStreak

SELECT  
		cgm.seasonYear,
		cgm.productGrouping,
		cgm.dimCustomerMasterId,
		cgm.consecGamesMissed,
		ISNULL(a.numOccurrences,0) numOccurrences
INTO #customerBucketDetails
FROM #customerBuckets cgm
    LEFT OUTER JOIN (
        SELECT 
            seasonYear, 
            dimCustomerMasterId, 
            productGrouping,
            CASE WHEN consecGamesMissed > 2 THEN '>2' ELSE CAST(consecGamesMissed AS VARCHAR) END consecGamesMissed,
            count(*) numOccurrences
        FROM (
            SELECT 
                seasonYear,
                productGrouping,
                dimCustomerMasterId,
                attendanceCount,
                eventDate,
                missedCount,
                CASE WHEN missedCount = 1 AND missedCount = lead(missedCount) OVER (PARTITION BY seasonYear, productGrouping, dimCustomerMasterId ORDER BY eventDate) THEN 0 ELSE consecGamesMissed END consecGamesMissed
            FROM 
                (SELECT 
                    seasonYear,
                    productGrouping,
                    dimCustomerMasterId,
                    attendanceCount,
                    eventDate,
                    missedCount,
                    SUM(missedCount) OVER (PARTITION BY seasonYear, productGrouping, dimCustomerMasterId, grp ORDER BY eventDate rows between unbounded preceding and unbounded following) as consecGamesMissed
                FROM
                    #missedStreakFinal) a
                ) a
            WHERE 
                consecGamesMissed > 0
            GROUP BY 
                a.seasonYear, 
                a.productGrouping, 
                a.dimCustomerMasterId, 
                CASE WHEN consecGamesMissed > 2 THEN '>2' ELSE CAST(consecGamesMissed AS VARCHAR) END
        ) a
    ON cgm.dimCustomerMasterId = a.dimCustomerMasterId
    AND cgm.consecGamesMissed = a.consecGamesMissed
    AND cgm.seasonYear = a.seasonYear
    AND cgm.productGrouping = a.productGrouping;

-- actual selection of missed games
SELECT 
    seasonYear, 
    dimCustomerMasterId, 
    productGrouping,
    SUM(missedGames_1) missed_games_1,
    SUM(missedGames_2) missed_games_2,
    SUM(missedGamesGreater_2) missed_games_over_2
INTO #missed_games_data
FROM 
    (SELECT 
        c.seasonYear, 
        c.dimCustomerMasterId, 
        c.productGrouping,
        CASE WHEN cbd.consecGamesMissed = '1' THEN cbd.numOccurrences END missedGames_1,
        CASE WHEN cbd.consecGamesMissed = '2' THEN cbd.numOccurrences END missedGames_2,
        CASE WHEN cbd.consecGamesMissed = '>2' THEN cbd.numOccurrences END missedGamesGreater_2
    FROM #customers c
        INNER JOIN #customerBucketDetails cbd
            ON c.dimCustomerMasterId = cbd.dimCustomerMasterId
            and c.seasonYear = cbd.seasonYear
            and c.productGrouping = cbd.productGrouping
    ) a
GROUP BY seasonYear, dimCustomerMasterId, productGrouping;


-- temporary scoring data
SELECT 
    scv.dimCustomerMasterId,
    s.seasonYear,
    p.productGrouping,
    dcm.distanceToVenue,
    dcm.sourceTenure as sourceTenure,
    e.eventDate,
    t.transactionDateTime as purchaseDate,
    cmd.minDate,
    t.reportedRev,
    case when a.ticketAcctId is not null then 1 else 0 end as attendanceCount,
    case when e.eventDate < me.maxEventDate then 1 else 0 end ticketCount
INTO #primaryTicketScoringDataTemp
FROM staging2.ticketHistory t
    join scv.customerMasterDetail scv 
        on t.customerNumber = scv.sourceCustomerId
        and scv.sourceSystemGroup = 'Ticketing'
    join scv.dimCustomerMaster dcm
        on scv.dimCustomerMasterId = dcm.dimCustomerMasterId
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
    join staging2.product p on t.productDescription = p.productGrouping
    join #customerMinDates cmd
        on scv.dimCustomerMasterId = cmd.dimCustomerMasterId
    join #maxEventDate me 
        on me.seasonYear= s.seasonYear  
    left join staging2.attendance a
        on a.eventId = t.eventId
        and a.sectionName = t.sectionName
        and a.rowName = t.rowName
        and a.seatNum = t.seatNum 
WHERE t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    -- AND s.isRegularSeason = 1
    AND t.reportedRev > 0
    AND CAST(s.seasonYear AS int) BETWEEN @start_year AND @end_year
    AND p.isPlanProduct = 1

-- scoring data
SELECT 
    -- sdt.lkupClientId,
    sdt.dimCustomerMasterId,
    sdt.seasonYear AS year,
    sdt.productGrouping,
    CAST(SUM(reportedRev) AS float) totalSpent,
    MAX(CASE WHEN attendanceCount > 0 THEN eventDate ELSE '1970-01-01' END) recentDate,
    CASE WHEN SUM(ticketCount) = 0 THEN 0 ELSE CAST(SUM(attendanceCount) AS float)/CAST(SUM(ticketCount) AS float) END attendancePercent,
    DATEDIFF(day,CASE WHEN MIN(purchaseDate) = '1900-01-01' THEN MIN(eventDate) ELSE MIN(purchaseDate) END, MIN(eventDate)) AS renewedBeforeDays,
    CASE WHEN SUM(reportedRev) > 0 THEN 'TRUE' ELSE 'FALSE' END isBuyer,
    CASE WHEN MIN(sourceTenure) IS NULL THEN DATEDIFF(DAY, MIN(minDate), MAX(eventDate)) ELSE (year(getdate()) - MIN(sourceTenure)) * 365 END AS source_tenure,
    DATEDIFF(day, MIN(minDate), MAX(eventDate)) tenure,
    avg(distanceToVenue) as distToVenue
INTO #primaryTicketScoringData
FROM #primaryTicketScoringDataTemp sdt
GROUP BY 
    -- sdt.lkupClientId,
    sdt.dimCustomerMasterId,
    sdt.seasonYear,
    sdt.productGrouping;

-- secondary
-- SELECT * 
-- INTO #secondaryTicketData
-- FROM (
--     SELECT DISTINCT
--         s.seasonYear, 
--         t.customerNumber,
--         p.productGrouping,
--         SUM(0) AS PostingRecords,
--         SUM(case when t.transactionType = 'RESALE' then 1 else 0 end) AS ResaleRecords,
--         SUM(case when t.transactionType = 'FORWARD' then 1 else 0 end) AS ForwardRecords
--     FROM staging2.ticketHistory t
--         join #events e on t.eventId = e.sourceEventId
--         join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
--         join staging2.product p on t.productDescription = p.productGrouping
--     WHERE t.transactionType in ('RESALE', 'FORWARD')
--         AND CAST(s.seasonYear AS int) BETWEEN @start_year AND @end_year
--     GROUP BY 
--         s.seasonYear, 
--         t.customerNumber, 
--         p.productGrouping 
-- ) a;


SELECT 
    scv.dimCustomerMasterId,
    seasonYear,
    productGrouping,
    count(t.customerNumber) numTickets
INTO #customerSeasonProductAgg
FROM staging2.ticketHistory t
    join scv.customerMasterDetail scv 
        on t.customerNumber = scv.sourceCustomerId
        and scv.sourceSystemGroup = 'Ticketing'
    join #events e on t.eventId = e.sourceEventId
    join staging2.season s on e.sourceSeasonId = s.sourceSeasonId
    join staging2.product p on t.productDescription = p.productGrouping
WHERE t.transactionType = 'PRIMARY SALE'
    and t.isActive = 1
    -- AND s.isRegularSeason = 1
    AND p.isPlanProduct = 1
    AND CAST(s.seasonYear AS int) BETWEEN @start_year AND @end_year
GROUP BY scv.dimCustomerMasterId, productGrouping, seasonYear;

SELECT a.dimCustomerMasterId, a.seasonYear, a.productGrouping, COUNT(b.seasonYear) AS isNextYearBuyer
INTO #nextyearbuyer
FROM #customerSeasonProductAgg a
    LEFT JOIN #customerSeasonProductAgg b 
    ON a.dimCustomerMasterId = b.dimCustomerMasterId 
    AND (a.seasonYear + 1) = b.seasonYear 
    AND a.productGrouping = b.productGrouping
GROUP BY a.dimCustomerMasterId, a.seasonYear, a.productGrouping;

SELECT DISTINCT 
    sd.dimCustomerMasterId,
    sd.year,
    sd.productGrouping,
    ROUND(sd.totalSpent,2) AS totalSpent,
    sd.recentDate,
    ROUND(sd.attendancePercent,2) AS attendancePercent,
    sd.renewedBeforeDays,
    sd.source_tenure,
    sd.tenure,
    ROUND(sd.distToVenue,2) AS distToVenue,
    CASE WHEN a.attended IS NULL OR p.bought IS NULL THEN 0 ELSE p.bought - a.attended END AS recency,
    CASE WHEN mgd.missed_games_1 IS NULL THEN 0 ELSE ROUND(mgd.missed_games_1,2)  END AS missed_games_1,
    CASE WHEN mgd.missed_games_2 IS NULL THEN 0 ELSE ROUND(mgd.missed_games_2,2)  END AS missed_games_2,
    CASE WHEN mgd.missed_games_over_2 IS NULL THEN 0 ELSE ROUND(mgd.missed_games_over_2,2) END AS missed_games_over_2,
    --CASE WHEN md.ClickEmail IS NULL THEN 0 ELSE md.ClickEmail END AS click_link,
    --CASE WHEN md.OpenEmail IS NULL THEN 0 ELSE md.OpenEmail END AS open_email,
    --CASE WHEN md.SendEmail IS NULL THEN 0 ELSE md.SendEmail END AS send_email,
    --CASE WHEN smd.PostingRecords IS NULL THEN 0 ELSE smd.PostingRecords END AS posting_records, 
    --CASE WHEN smd.ResaleRecords IS NULL THEN 0 ELSE smd.ResaleRecords END AS resale_records, 
    -- CASE WHEN smd.ForwardRecords IS NULL THEN 0 ELSE smd.ForwardRecords END AS forward_records,
    -- CASE WHEN (md.SendEmail IS NULL OR md.SendEmail = 0 OR md.OpenEmail IS NULL) THEN 0 
    --     ELSE ROUND(md.OpenEmail * 1.0/md.SendEmail,2)  END openToSendRatio,
    -- CASE WHEN (md.SendEmail IS NULL OR md.SendEmail = 0 OR md.ClickEmail IS NULL) THEN 0 
    --     ELSE ROUND(md.ClickEmail * 1.0/md.SendEmail ,2) 
    -- END AS clickToSendRatio,
    -- CASE WHEN (md.OpenEmail IS NULL OR md.OpenEmail = 0 OR md.ClickEmail IS NULL) THEN 0 
    --     ELSE ROUND(md.ClickEmail * 1.0/md.OpenEmail ,2) 
    -- END AS clickToOpenRatio,
    -- CASE WHEN dgd.gender IS NULL THEN 'Unknown' ELSE dgd.gender END AS gender,
    -- CASE WHEN tpd.phonecall IS NULL THEN 0 ELSE tpd.phonecall END AS phonecall ,
    -- CASE WHEN tpc.inperson_contact IS NULL THEN 0 ELSE tpc.inperson_contact END AS inperson_contact , 
    cg.isNextYearBuyer AS isNextYear_Buyer
from #primaryTicketScoringData sd
    left join #totalGames tg
        on sd.dimCustomerMasterId = tg.dimCustomerMasterId
        and sd.year = tg.seasonYear
        and sd.productGrouping = tg.productGrouping
    left join #attendance a
        on sd.dimCustomerMasterId = a.dimCustomerMasterId
        and sd.year = a.seasonYear
        and sd.productGrouping = a.productGrouping
    left join #purchase p
        on sd.dimCustomerMasterId = p.dimCustomerMasterId
        and sd.year = p.seasonYear
        and sd.productGrouping = p.productGrouping
    left join #missed_games_data mgd
        on sd.dimCustomerMasterId = mgd.dimCustomerMasterId
        and sd.year = mgd.seasonYear
        and sd.productGrouping = mgd.productGrouping
    -- left join #secondaryTicketData smd
    --     on sd.dimCustomerMasterId = smd.dimCustomerMasterId
    --     and sd.year = smd.seasonYear
    --     and sd.productGrouping = smd.productGrouping
    inner join #nextyearbuyer cg 
        on cg.dimCustomerMasterId = sd.dimCustomerMasterId
        and cg.seasonYear= sd.year
        and cg.productGrouping= sd.productGrouping
