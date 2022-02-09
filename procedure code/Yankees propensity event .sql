SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE    [ds].[getPropensityEventScoring_new] 
	@lkupClientId int
with recompile
as
begin
--declare @lkupClientId int = 11
	-- exec [DS].[getPropensityEventScoring_new] 53
	set nocount on;
	set transaction isolation level read uncommitted;

	declare @datenow datetime = dateadd(day, datediff(day, 0, getdate()), 0);

	-- average distance to venue
	declare @avgdist_reg float
	select
		@avgdist_reg = avg(distanceToVenue)
	from dw.dimCustomerMaster
	where
		lkupClientId = @lkupClientId
		and distanceToVenue is not null
        and inMarket ='True'
	option (optimize for unknown)

	-- get events that have attendance
--	declare @max_event_date date;

	select a.seasonYear,
        max(eventDate) as max_event_date
		--@max_event_date = max(eventDate) 
        into #maxEventDate
	from (
		select fts.seasonYear ,
			max(fts.eventDate) eventDate
            -- select top 10 * 
		from dw.cohortPurchase fts
			join dw.dimCustomerMaster de on fts.dimCustomerMasterId = de.dimCustomerMasterId
		where
			fts.lkupClientId = @lkupClientId
			and fts.isRegularSeason = 1
            and fts.isRenewalEvent = 0
			and fts.eventDate < @datenow
			and fts.subProductName = 'Online Individual Game'
            and fts.dimCustomerMasterId <> -1
            and de.inMarket ='True'
            and not exists (select 'true'
					from dw.cohortPurchase fts2
						inner join dw.dimCustomerMaster ds2
							on fts2.dimCustomerMasterId = ds2.dimCustomerMasterId
						WHERE fts2.lkupClientId = @lkupClientId
                        and fts2.isRegularSeason = 1
                        and ds2.inMarket ='True'
                        and fts2.dimCustomerMasterId <> -1
                        and fts2.subProductName <> 'Online Individual Game'
					and fts.dimCustomerMasterId = fts2.dimCustomerMasterId
					and fts.seasonYear = fts2.seasonYear)
		group by
			fts.eventName,fts.seasonYear
		having
			sum(attendanceCount) > 0
	) a
    GROUP BY a.seasonYear
	option (optimize for unknown)


	-- first purchase date by customer
	select
		fts.dimCustomerMasterId,
		min(fts.purchaseDate) as minDate
	into #customerMinDates
	from dw.cohortPurchase fts
    inner join dw.dimCustomerMaster ms 
    on ms.dimCustomerMasterId = fts.dimCustomerMasterId
	where fts.lkupClientId = @lkupClientId
		and fts.isRegularSeason = 1
            and fts.isRenewalEvent = 0
            and ms.inMarket ='True'
            and fts.dimCustomerMasterId <> -1
			and fts.subProductName = 'Online Individual Game'
            and not exists (select 'true'
					from dw.cohortPurchase fts2
						inner join dw.dimCustomerMaster ds2
							on fts2.dimCustomerMasterId = ds2.dimCustomerMasterId
						WHERE fts2.lkupClientId = @lkupClientId
                        and fts2.isRegularSeason = 1
                        and ds2.inMarket = 'True'
                        and fts2.dimCustomerMasterId <> -1
                        and fts2.subProductName <> 'Online Individual Game'
					and fts.dimCustomerMasterId = fts2.dimCustomerMasterId
					and fts.seasonYear = fts2.seasonYear)
	group by
		fts.dimCustomerMasterId
	option (optimize for unknown);
	
	-- total attended games by customer, season and product
	select
		fts.dimCustomerMasterId,
		fts.seasonYear,
		count(distinct fts.eventName) as totalGames
	into #totalGames
	from dw.cohortPurchase fts
    INNER JOIN dw.dimCustomerMaster ms 
    on ms.dimCustomerMasterId = fts.dimCustomerMasterId
	where
		fts.lkupClientId = @lkupClientId
		and fts.attendanceCount > 0
		and fts.isRegularSeason = 1
            and fts.isRenewalEvent = 0
            and ms.inMarket ='True'
            and fts.dimCustomerMasterId <> -1
			and fts.subProductName = 'Online Individual Game'
            and not exists (select 'true'
					from dw.cohortPurchase fts2
						inner join dw.dimCustomerMaster ds2
							on fts2.dimCustomerMasterId = ds2.dimCustomerMasterId
						WHERE fts2.lkupClientId = @lkupClientId
                        and fts2.isRegularSeason = 1
                        and fts2.dimCustomerMasterId <> -1
                        and ds2.inMarket ='True'
                        and fts2.attendanceCount > 0
                        and fts2.subProductName <> 'Online Individual Game'
					and fts.dimCustomerMasterId = fts2.dimCustomerMasterId
					and fts.seasonYear = fts2.seasonYear)
	group by
		fts.dimCustomerMasterId,
		fts.seasonYear
    option (optimize for unknown)

-- ? why customerNumber
	-- recency info by customer, season and product
	select
		dimCustomerMasterId,
		seasonYear,
		productGrouping,
		row_number() over (partition by dimCustomerMasterId, seasonYear, productGrouping order by eventDate asc) as rowNum,
		attended 
	into #recency
	from(select fts.dimCustomerMasterId,
			fts.seasonYear,
			fts.productGrouping,
			fts.eventDate,
			max(isnull(fts.attendanceCount ,0)) attended
		from dw.cohortPurchase fts
			join dw.dimCustomerMaster dc
				on fts.dimCustomerMasterId = dc.dimCustomerMasterId
            join #maxEventDate me 
            on me.seasonYear= fts.seasonYear
		where
			fts.lkupClientId = @lkupClientId
		    and fts.isRegularSeason = 1
            and fts.isRenewalEvent = 0
            and fts.dimCustomerMasterId <> -1
            and dc.inMarket ='True'
			and fts.subProductName = 'Online Individual Game'
            and not exists (select 'true'
					from dw.cohortPurchase fts2
						inner join dw.dimCustomerMaster ds2
							on fts2.dimCustomerMasterId = ds2.dimCustomerMasterId
						WHERE fts2.lkupClientId = @lkupClientId
                        and fts2.isRegularSeason = 1
                        and fts2.dimCustomerMasterId <> -1
                        and ds2.inMarket ='True'
                        and fts2.attendanceCount > 0
                        and fts2.subProductName <> 'Online Individual Game'
					and fts.dimCustomerMasterId = fts2.dimCustomerMasterId
					and fts.seasonYear = fts2.seasonYear)
			and fts.eventDate < me.max_event_date
		group by
			fts.dimCustomerMasterId,
            fts.productGrouping,
			fts.seasonYear,
			fts.eventDate) a
	option (optimize for unknown)
	

	-- latest attended event
	select
		dimCustomerMasterId,
		seasonYear,
		productGrouping,
		max(rowNum) as attended
	into #attendance
	from #recency
	where
		attended = 1
	group by
		dimCustomerMasterId,
		seasonYear,
		productGrouping;

	-- latest purchased event
	select
		dimCustomerMasterId,
		seasonYear,
		productGrouping,
		max(rowNum) as bought
	into #purchase
	from #recency
	group by
		dimCustomerMasterId,
		seasonYear,
		productGrouping;


	
	-- temporary scoring data
	select fts.dimCustomerMasterId,
        fts.eventName,
		dc.inMarket,
		fts.seasonYear,
		fts.productGrouping,
		dc.distanceToVenue,
		fts.eventDate,
		fts.purchaseDate,
		cmd.minDate,
		fts.revenue,
		dc.sourceTenure,
		isnull(fts.attendanceCount,0)  attendanceCount,
		case
			when fts.eventDate < me.max_event_date then fts.ticketCount
			else 0
		end ticketCount
	into #scoringDataTemp
	from dw.cohortPurchase fts
		join dw.dimCustomerMaster dc
			on fts.dimCustomerMasterId = dc.dimCustomerMasterId
		join #customerMinDates cmd
			on fts.dimCustomerMasterId = cmd.dimCustomerMasterId
        join #maxEventDate me 
            on me.seasonYear= fts.seasonYear
            
	where
			fts.lkupClientId = @lkupClientId
		    and fts.isRegularSeason = 1
            and fts.isRenewalEvent = 0
            and fts.dimCustomerMasterId <> -1
            and dc.inMarket ='True'
			and fts.subProductName = 'Online Individual Game'
            and not exists (select 'true'
					from dw.cohortPurchase fts2
						inner join dw.dimCustomerMaster ds2
							on fts2.dimCustomerMasterId = ds2.dimCustomerMasterId
						WHERE fts2.lkupClientId = @lkupClientId
                        and fts2.isRegularSeason = 1
                        and fts2.attendanceCount > 0
                        and fts2.dimCustomerMasterId <> -1
                        and ds2.inMarket ='True'
                        and fts2.subProductName <> 'Online Individual Game'
					and fts.dimCustomerMasterId = fts2.dimCustomerMasterId
					and fts.seasonYear = fts2.seasonYear)
	option (optimize for unknown)


	-- scoring data
	select
		sdt.dimCustomerMasterId,
        sdt.eventName,
        sdt.inMarket,
		sdt.seasonYear as year,
		sdt.productGrouping,
		cast(sum(case
			when (@lkupClientId = 9 and productGrouping like '%Club%') then revenue - 18
			else revenue
		end) as float) totalSpent,
		max(case
			when attendanceCount = 1 then eventDate
			else '1970-01-01'
		end) recentDate,
		case
			when sum(ticketCount) = 0 then 0
			else cast(sum(attendanceCount) as float)/cast(sum(ticketCount) as float)
		end attendancePercent,
		DATEDIFF(day,case when min(purchaseDate) = '1900-01-01' then min(eventDate) else min(purchaseDate) end, min(eventDate)) as renewedBeforeDays,
		case
			when sum(revenue) > 0 then 'TRUE'
			else 'FALSE'
		end isBuyer,
		case when min(sourceTenure) is null then DATEDIFF(DAY, min(minDate), max(eventDate)) else (Year(@datenow)- min(sourceTenure))*365 end as source_tenure,
		datediff(day, min(minDate), max(eventDate)) tenure,
		case
			when avg(distanceToVenue) is null then @avgdist_reg
			else avg(distanceToVenue)
		end distToVenue
	into #scoringData
	from #scoringDataTemp sdt
	group by
		sdt.dimCustomerMasterId,
        sdt.inMarket,
        sdt.eventName,
		sdt.seasonYear,
		sdt.productGrouping;

	-- START OF MARKETING
	-- get dates for marketing
	declare @minMarketingDate date = (
		select min(date) 
		from dw.factMarketingActivity f 
			join dw.dimDate dd on f.dimDateId = dd.dimDateId
		where lkupClientId = @lkupClientId
	)

	-- select all dates?
	select dimDateId,
		Date, 
		case 
			when Date between seasonStartDate and seasonEndDate then year
			when Date < seasonStartDate then year-1
			when Date > seasonEndDate then year+1 
		end as seasonYear
	into #campaignSeason
	from dw.dimDate d 
		left join dw.dimSeason s on d.year = s.seasonYear
	where s.lkupClientId = @lkupClientId
		and s.isRegularSeason = 1
		and s.isSuiteSeason = 0
		and d.date between @minMarketingDate and @datenow
	option (optimize for unknown)

	-- get marketing activities
	select fma.dimCustomerMasterId,
        --dc.sourceTicketingIds customerNumber, 
        (case 
            when dma.isSendEmail = 1 then 'Send Email'
            when dma.isOpenEmail = 1 then 'Open Email'
            when dma.isClickEmail = 1 then 'Click Email'
            when dma.isUnsubscribe = 1 then 'Unsubscribe Email'
            else dma.activityName
        end) activityName, 
        seasonYear, 
        sum(activityCount) numActivities
	into #marketoActivities
	from dw.factMarketingActivity fma
		inner join dw.dimMarketingActivity dma on fma.dimMarketingActivityId=dma.dimMarketingActivityId
		inner join dw.dimCustomer dc on fma.dimCustomerId=dc.dimCustomerId
		left join #campaignSeason cs on fma.dimDateId = cs.dimDateId
	where fma.lkupClientId=@lkupClientId
		--and seasonYear = @year
	group by 
        fma.dimCustomerMasterId, 
        seasonYear, 
        (case 
            when dma.isSendEmail = 1 then 'Send Email'
            when dma.isOpenEmail = 1 then 'Open Email'
            when dma.isClickEmail = 1 then 'Click Email'
            when dma.isUnsubscribe = 1 then 'Unsubscribe Email'
            else dma.activityName
        end)
	option (optimize for unknown)


	-- final select for marketing
	select * 
	into #marketoData 
	from #marketoActivities
	pivot ( 
		sum(numActivities) for activityName in ([Click Email],[Fill Out Form],[Open Email],[Send Email],[Unsubscribe Email])
	) piv
	order by dimCustomerMasterId, seasonYear;
	-- END OF MARKETING

	
 drop table if exists #credit_candidates;    
    select
        dimCustomerMasterId,
        creditsIssued,
        creditsUsed
    into #credit_candidates
    from(
        select 
            dimCustomerMasterId,
            sum(case when creditApplied < 0 then -creditApplied else 0 end) creditsUsed,
            sum(case when creditApplied > 0 then creditApplied else 0 end) creditsIssued
        from dw.rptCredits
        where lkupClientId= @lkupClientId
        group by dimCustomerMasterId
    )a
    where a.creditsIssued > creditsUsed

     drop table if exists #credit_remained; 
     select * into #credit_remained 
     from (select distinct
        rr.dimCustomerMasterId,
        rr.refundApplied,
        cc.creditsIssued,
        cc.creditsUsed,
        creditsIssued - creditsUsed as creditsRemaining,
        ((creditsIssued - creditsUsed) - (-refundApplied)) as creditsRemainingAfterRefundUse,
        ROW_NUMBER() OVER(PARTITION BY rr.dimCustomerMasterId ORDER BY refundDateTime desc) AS Rownum
        -- select *
    from dw.rptRefunds rr
    join #credit_candidates cc on cc.dimCustomerMasterId = rr.dimCustomerMasterId
    where ((creditsIssued - creditsUsed) - (-refundApplied)) > 0
    and lkupClientId= @lkupClientId
    ) b
    where Rownum = 1

    
     select s.seasonYear, max(cast(gameNumber as int)) NumberofGamesPerSeason 
     into #TmpNumberofGamesPerSeason
     from dw.dimevent e 
     inner join dw.dimseason s
     on e.sourceSeasonId = s.sourceSeasonId
      where isRenewalEvent = 0
      and isRegularSeason = 1
      group by s.seasonYear


      select f.dimCustomerMasterId, e.tier as tier,f.seasonYear,COUNT(*) tierCNT
into  #cntTier
from [dw].[cohortPurchase] f
join dw.dimCustomerMaster dc
    on f.dimCustomerMasterId = dc.dimCustomerMasterId
join  DataScience.yankees.eventTiersSeason e 
    on e.eventDate = cast(f.eventDate as date)      
    and f.seasonYear = e.seasonYear     
where f.lkupClientId = @lkupClientId
    and f.dimCustomermasterId <> -1
    and dc.inMarket='True'
    and f.isRegularSeason = 1
    and f.productGrouping ='Online Individual Game'
    and not exists (select 'true'
                from [dw].[cohortPurchase] f2   
                inner join dw.dimCustomerMaster m2 
                    on f2.dimCustomerMasterId = m2.dimCustomerMasterId
                where f.lkupClientId = @lkupClientId
                and f2.isRegularSeason = 1
                and f2.isplanproduct = 1
                and f2.dimCustomermasterId <> -1
                and m2.inMarket ='True'
                and f2.productGrouping <> 'Online Individual Game'
                and f.dimCustomerMasterId = f2.dimCustomerMasterId
                and f.seasonYear = f2.seasonYear)
    group by f.dimCustomerMasterId, e.tier,f.seasonYear


  select dimCustomerMasterId,seasonYear,tier 
into #tierfinal
 from (
SELECT dimCustomerMasterId, t.tier, seasonYear, tierCNT, ROW_NUMBER() OVER (partition by dimCustomerMasterId, seasonYear ORDER BY tierCNT desc, tier) as select_me
FROM #cntTier t
) aa 
where aa.select_me =1
--order by seasonYear, tier 


select tf.dimCustomerMasterId,tf.seasonYear,tf.tier currentYearTier,tf2.tier nextYearTier 
into #nextYearTier
from #tierfinal tf
left join #tierfinal tf2
on tf.dimCustomerMasterId= tf2.dimCustomerMasterId
and tf2.seasonYear = tf.seasonYear +1

    drop table if exists #customerSeasonProductAgg

    select dimCustomerMasterId, seasonYear,de.eventName,de.dimEventId,dp.productGrouping, sum(fts.ticketCount) numTickets
    into #customerSeasonProductAgg
    	from dw.factTicketSold fts
			join dw.dimEvent de on fts.dimEventId = de.dimEventId
			join dw.dimSeason ds on fts.dimSeasonId = ds.dimSeasonId
			join dw.dimProduct dp on fts.dimProductId = dp.dimProductId
		where
			fts.lkupClientId = @lkupClientId
			and ds.isRegularSeason = 1
            and de.isRenewalEvent = 0
			and dp.isIndividual = 1
            and dp.productGrouping ='Online Individual Game'
            and not exists (select 'true'
					from dw.factTicketSold fts2
						inner join dw.dimSeason ds2
							on fts2.dimSeasonId = ds2.dimSeasonId
							and ds2.isRegularSeason = 1
							and ds2.isRenewalSeason = 0
						inner join dw.dimProduct dp2
							on fts2.dimProductId = dp2.dimProductId
							and dp2.isIndividual = 0
							and dp2.isComp = 0
					where fts.dimCustomerMasterId = fts2.dimCustomerMasterId
                    and dp2.productGrouping <> 'Online Individual Game'
					and ds.seasonYear = ds2.seasonYear)
    group by dimCustomerMasterId,dp.productGrouping,de.dimEventId, seasonYear,de.eventName

   drop table if exists #NextGameBuyer 
    select a.dimCustomerMasterId, a.seasonYear,a.eventName, a.productGrouping,a.dimEventId, count(b.seasonYear) as isNextGameBuyer
    into #NextGameBuyer
    from #customerSeasonProductAgg a
        left join #customerSeasonProductAgg b on a.dimCustomerMasterId = b.dimCustomerMasterId and (a.dimEventId + 1) = b.dimEventId and a.seasonYear = b.seasonYear and a.productGrouping = b.productGrouping
    group by a.dimCustomerMasterId, a.seasonYear,a.eventName, a.productGrouping,a.dimEventId
    order by a.dimCustomerMasterId, a.seasonYear,a.eventName, a.productGrouping,a.dimEventId
   
   -- DELETE FROM dataScience.ds.retentionscoring where lkupclientId= @lkupClientId --and year=@year

	select DISTINCT @lkupclientid as lkupClientId,
		sd.*,
		case
			when tg.totalGames is null then 0
			else tg.totalGames
		end totalGames,
		case
			when a.attended is null or p.bought is null then 0
			else p.bought - a.attended
		end recency,
		case
			when md.[Click Email] is null then 0
			else md.[Click Email]
		end click_link,
		case
			when md.[Fill Out Form] is null then 0
			else md.[Fill Out Form]
		end fill_out_form,
		case
			when md.[Open Email] is null then 0 
			else md.[Open Email]
		end open_email,
		case
			when md.[Send Email] is null then 0 
			else md.[Send Email]
		end send_email,
		case
			when md.[Unsubscribe Email] is null then 0
			else md.[Unsubscribe Email]
		end unsubscribe_email,
		case
			when (md.[Send Email] is null or md.[Send Email] = 0 or md.[Open Email] is null) then 0 
			else md.[Open Email]*1.0/md.[Send Email] 
		end openToSendRatio,
		case
			when (md.[Send Email] is null or md.[Send Email] = 0 or md.[Click Email] is null) then 0 
			else md.[Click Email]*1.0/md.[Send Email] 
		end clickToSendRatio,
		case
			when (md.[Open Email] is null or md.[Open Email] = 0 or md.[Click Email] is null) then 0 
			else md.[Click Email]*1.0/md.[Open Email] 
		end clickToOpenRatio,
		
        isnull(cr.creditsRemainingAfterRefundUse,0) AS credits_after_refund,
        g.NumberofGamesPerSeason,
        cg.isNextGameBuyer ,
        yt.nextYearTier
	from #scoringData sd
		left join #totalGames tg
			on sd.dimCustomerMasterId = tg.dimCustomerMasterId
			and sd.year = tg.seasonYear
		left join #attendance a
			on sd.dimCustomerMasterId = a.dimCustomerMasterId
			and sd.year = a.seasonYear
			and sd.productGrouping = a.productGrouping
		left join #purchase p
			on sd.dimCustomerMasterId = p.dimCustomerMasterId
			and sd.year = p.seasonYear
			and sd.productGrouping = p.productGrouping
		left join #marketoData md
			on sd.dimCustomerMasterId = md.dimCustomerMasterId
			and sd.year = md.seasonYear
        left join #credit_remained cr 
        on cr.dimCustomerMasterId= sd.dimCustomerMasterId
        inner join #NextGameBuyer cg 
        on cg.dimCustomerMasterId= sd.dimCustomerMasterId
        and cg.seasonYear= sd.year
        and cg.productGrouping= sd.productGrouping
        and cg.eventName = sd.eventName
        left join #TmpNumberofGamesPerSeason g 
        on g.seasonYear = sd.year
        left join #nextYearTier yt 
        on yt.dimCustomerMasterId = sd.dimCustomerMasterId
        and yt.seasonYear= sd.year
	order by sd.year;


	-- cleanup
	drop table if exists #customerMinDates;
	drop table if exists #totalGames;
	drop table if exists #recency;
	drop table if exists #attendance;
	drop table if exists #purchase;
	drop table if exists #scoringDataTemp;
	drop table if exists #scoringData;

	-- missed games temps
	drop table if exists #customerData;
	drop table if exists #customers;
	drop table if exists #customerBuckets;
	drop table if exists #customerBucketDetails;

	-- secondary market tables
	drop table if exists #activities;
	drop table if exists #temp1;
	drop table if exists #temp2;
	drop table if exists #campaignSeason;
	drop table if exists #marketoActivities;
	drop table if exists #marketoData;
    drop table if exists #credit_candidates
    drop table if exists #credit_remained

	-- live analytics
	drop table if exists #fscust;
	drop table if exists #demoData;
    drop table if exists #customerSeasonProductAgg;
    drop table if exists #nextyearbuyer
    drop table if exists #nextYearTier
    drop table if exists #tierfinal
end

GO
