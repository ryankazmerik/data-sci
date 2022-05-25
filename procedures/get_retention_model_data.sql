CREATE OR REPLACE PROCEDURE dw.getretentionmodeldata(_lkupclientid int4, start_year int4, end_year int4, rs_out refcursor)
	LANGUAGE plpgsql
AS $$
	
	
	
	
	
	
	
	-- find year to begin training data from
	declare datenow date := current_date;
	    avgdistreg float = (SELECT AVG(distanceToVenue) 
	    				FROM dw.cohortCustomer c
						WHERE c.lkupClientId = _lkupclientid
							AND distanceToVenue IS NOT NULL);
						
		minMarketingDate date = (SELECT MIN(activityDate) FROM dw.cohortMarketing f WHERE f.lkupClientId = _lkupclientid);

BEGIN

	 	-- get events that have attendance
	
     
DROP TABLE IF EXISTS #maxEventDate;
DROP TABLE IF EXISTS #customerMinDates;
DROP TABLE IF EXISTS #totalGames;
DROP TABLE IF EXISTS #recency;
DROP TABLE IF EXISTS #attendance;
DROP TABLE IF EXISTS #purchase;
DROP TABLE IF EXISTS #customerData;
DROP TABLE IF EXISTS #customers;
DROP TABLE IF EXISTS #consecGamesMissedTbl;
DROP TABLE IF EXISTS #missedStreak;
DROP TABLE IF EXISTS #missedStreakFinal;
DROP TABLE IF EXISTS #customerBucketDetails;
DROP TABLE IF EXISTS #customerbuckets;
DROP TABLE IF EXISTS #scoringDataTemp;
DROP TABLE IF EXISTS #scoringData;
DROP TABLE IF EXISTS #seasonDates;
DROP TABLE IF EXISTS #marketoData;
DROP TABLE IF EXISTS #secondaryData;
DROP TABLE IF EXISTS #touchPointData;
DROP TABLE IF EXISTS #WebEngagement;
DROP TABLE IF EXISTS #fscust;
DROP TABLE IF EXISTS #demographicData;
DROP TABLE IF EXISTS #TmpNumberofGamesPerSeason;
DROP TABLE IF EXISTS #customerSeasonProductAgg;
DROP TABLE IF EXISTS #nextyearbuyer;
DROP TABLE IF EXISTS #TmpNumberofGamesPerSeason;
DROP table if exists #marketing_dates;
DROP TABLE IF EXISTS #touchPointDataCall;
DROP TABLE IF EXISTS #touchPointDataSignificant;
   

	SELECT a.seasonYear,
           MAX(eventDate) AS max_event_date
    INTO #maxEventDate
	FROM (
		    SELECT fts.seasonYear ,
		           MAX(fts.eventDate) eventDate
            FROM dw.cohortPurchase fts
		    WHERE fts.lkupClientId = _lkupclientid
		    	AND fts.isRegularSeason = 1
                AND fts.isRenewalEvent = 0
		    	AND fts.eventDate < datenow
		    	AND fts.isPlanProduct = 1
		    	AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
		    GROUP BY fts.eventName,fts.seasonYear
		    HAVING SUM(attendanceCount) > 0
	) a
    GROUP BY a.seasonYear;
	

	-- first purchase date by customer

    DROP TABLE IF EXISTS #customerMinDates;

	SELECT
		fts.dimCustomerMasterId,
		min(fts.purchaseDate) as minDate
	INTO #customerMinDates
	FROM dw.cohortPurchase fts
	WHERE fts.lkupClientId = _lkupclientid
		AND fts.isRegularSeason = 1
		AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
	GROUP BY fts.dimCustomerMasterId;

	-- total attended games by customer, season and product

DROP TABLE IF EXISTS #totalGames;

	SELECT
		fts.dimCustomerMasterId,
		fts.seasonYear,
		fts.productGrouping,
		COUNT(DISTINCT fts.eventName) AS totalGames
	INTO #totalGames
	FROM dw.cohortPurchase fts
	WHERE fts.lkupClientId = _lkupclientid
		AND fts.attendanceCount > 0
		AND fts.isRegularSeason = 1
		AND fts.isPlanProduct = 1
		AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
	GROUP BY
		fts.dimCustomerMasterId,
		fts.seasonYear,
		fts.productGrouping;


	-- recency info by customer, season and product


	SELECT
		dimCustomerMasterId,
		seasonYear,
		productGrouping,
		row_number() OVER (PARTITION BY dimCustomerMasterId, seasonYear, productGrouping ORDER BY eventDate asc) AS rowNum,
		attended 
	INTO #recency
	FROM(
        SELECT fts.dimCustomerMasterId,
			fts.seasonYear,
			fts.productGrouping,
			fts.eventDate,
			MAX(fts.attendanceCount) attended
		FROM dw.cohortPurchase fts
            JOIN #maxEventDate me 
            ON me.seasonYear= fts.seasonYear
		WHERE
			fts.lkupClientId = _lkupclientid
			AND fts.isRegularSeason = 1
			AND fts.isPlanProduct = 1
			AND fts.revenue > 0
			AND fts.eventDate < me.max_event_date
			AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
		GROUP BY
			fts.dimCustomerMasterId,
			fts.seasonYear,
			fts.productGrouping,
			fts.eventDate) a;
		
	-- latest attended event


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
	
	-- START OF MISSED GAMES
	-- Missed games customer data
	SELECT  
		fts.seasonYear,
        fts.dimCustomerMasterId,
		fts.productGrouping,
		fts.eventDate,
		MAX( fts.attendanceCount) attendanceCount,
		MAX(CASE WHEN fts.attendanceCount = 1 THEN 0 ELSE 1 END) missedCount
	INTO #customerData
	FROM dw.cohortPurchase fts
    INNER JOIN #maxEventDate me ON me.seasonYear= fts.seasonYear
	WHERE fts.lkupClientId = _lkupclientid
		AND fts.isPlanProduct = 1
		AND fts.isRegularSeason = 1
		AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
		AND fts.eventDate < me.max_event_date
	GROUP BY 
		fts.seasonYear,
        fts.dimCustomerMasterId,
		fts.eventDate,
		fts.productGrouping;
	
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
		SUM(changed) OVER (PARTITION BY seasonYear, productGrouping, dimCustomerMasterId ORDER BY eventDate rows between unbounded preceding and unbounded following) grp
	INTO #missedStreakFinal
	FROM #missedStreak;

	SELECT  
		cgm.seasonYear,
		cgm.productGrouping,
		cgm.dimCustomerMasterId,
		cgm.consecGamesMissed,
		ISNULL(a.numOccurrences,0) numOccurrences
	INTO #customerBucketDetails
	FROM 
		#customerBuckets cgm
	LEFT OUTER JOIN 
		(SELECT seasonYear, dimCustomerMasterId, productGrouping,
			CASE WHEN consecGamesMissed > 2 THEN '>2' ELSE CAST(consecGamesMissed AS VARCHAR) END consecGamesMissed,
			count(*) numOccurrences
		FROM 
			(SELECT 
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
				a.seasonYear, a.productGrouping, a.dimCustomerMasterId, 
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
	GROUP BY seasonYear, dimCustomerMasterId, productGrouping
	;

	-- END OF MISSED GAMES


-- temporary scoring data
	SELECT fts.lkupClientId,
	fts.dimCustomerMasterId,
		fts.seasonYear,
		fts.productGrouping,
		dc.distanceToVenue,
		fts.eventDate,
		fts.purchaseDate,
		cmd.minDate,
		fts.revenue,
		dc.sourceTenure,
	    fts.attendanceCount AS attendanceCount,
		CASE
			WHEN fts.eventDate < me.max_event_date THEN fts.ticketCount
			ELSE 0
		END ticketCount
	INTO #scoringDataTemp
	FROM dw.cohortPurchase fts
		JOIN dw.cohortCustomer dc
			ON fts.dimCustomerMasterId = dc.dimCustomerMasterId
		JOIN #customerMinDates cmd
			ON fts.dimCustomerMasterId = cmd.dimCustomerMasterId
        JOIN #maxEventDate me 
            ON me.seasonYear= fts.seasonYear  
	WHERE fts.lkupClientId = _lkupclientid
		AND fts.dimCustomermasterId <> -1
		AND fts.isRegularSeason = 1
		AND fts.revenue > 0
		AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
		AND fts.isPlanProduct = 1;


	-- scoring data
	SELECT sdt.lkupClientId,
		sdt.dimCustomerMasterId,
		sdt.seasonYear AS year,
		sdt.productGrouping,
		CAST(SUM(CASE WHEN (lkupClientId = 9 AND productGrouping LIKE '%Club%') THEN revenue - 18 ELSE revenue END) AS float) totalSpent,
		MAX(CASE WHEN attendanceCount = 1 THEN eventDate ELSE '1970-01-01' END) recentDate,
		CASE WHEN SUM(ticketCount) = 0 THEN 0 ELSE CAST(SUM(attendanceCount) AS float)/CAST(SUM(ticketCount) AS float) END attendancePercent,
		DATEDIFF(day,CASE WHEN MIN(purchaseDate) = '1900-01-01' THEN MIN(eventDate) ELSE MIN(purchaseDate) END, MIN(eventDate)) AS renewedBeforeDays,
		CASE WHEN SUM(revenue) > 0 THEN 'TRUE' ELSE 'FALSE' END isBuyer,
		CASE WHEN MIN(sourceTenure) IS NULL THEN DATEDIFF(DAY, MIN(minDate), MAX(eventDate)) ELSE (extract(year from datenow) - MIN(sourceTenure))*365 END AS source_tenure,
		DATEDIFF(day, MIN(minDate), MAX(eventDate)) tenure,
		CASE WHEN AVG(distanceToVenue) IS NULL THEN avgdistreg ELSE avg(distanceToVenue) END distToVenue
	INTO #scoringData
	FROM #scoringDataTemp sdt
	GROUP BY sdt.lkupClientId,
		sdt.dimCustomerMasterId,
		sdt.seasonYear,
		sdt.productGrouping;
	
	-- START OF MARKETING
	-- get dates for marketing
	
 
	DROP TABLE IF EXISTS #seasonDates;

    SELECT DISTINCT seasonyear, seasonstartdate, seasonenddate
    INTO #seasonDates
    FROM dw.dimseason s
    WHERE s.lkupClientId = _lkupclientid
        AND s.isRegularSeason = 1
        AND s.isRenewalSeason = 0
        AND s.isSuiteSeason = 0
        AND CAST(s.seasonYear AS int) BETWEEN start_year AND end_year
    GROUP BY seasonyear, seasonstartdate, seasonenddate
    ;

    DROP TABLE IF EXISTS #marketoActivities;

    SELECT DISTINCT fma.dimCustomerMasterId,
        sd.seasonYear,
        SUM(numSends) SendEmail,
        SUM(numOpens) OpenEmail,
        SUM(numClicks) ClickEmail
    INTO #marketoData 
    FROM dw.cohortMarketing fma
        LEFT JOIN #seasonDates sd 
            ON fma.activityDate >= sd.seasonStartDate
            AND fma.activityDate <= sd.seasonEndDate
    WHERE fma.lkupClientId = _lkupclientid
    AND fma.activityDate BETWEEN minMarketingDate AND datenow
    GROUP BY 
        fma.dimCustomerMasterId, 
        seasonYear;

	-- END OF MARKETING
      
    -- START OF SECONDARY
	SELECT 
		* 
	INTO #secondaryData 
	FROM (
		SELECT DISTINCT
			fte.seasonYear, 
            fte.dimCustomerMasterId,
			fte.productGrouping,
			SUM(fte.postedCount) AS PostingRecords,
            SUM(fte.resoldCount) AS ResaleRecords,
            SUM(fte.forwardedCount) AS ForwardRecords
		FROM dw.cohortExchange fte
        INNER JOIN #seasonDates sd 
            ON fte.exchangeDate >= sd.seasonStartDate
            AND fte.exchangeDate <= sd.seasonEndDate
		WHERE 
			fte.lkupClientId = _lkupclientid
		GROUP BY 
			fte.seasonYear, 
			fte.dimCustomerMasterId, 
			fte.productGrouping ) a;
	
	-- END OF SECONDARY
			
	-- START OF CRM
DROP TABLE IF EXISTS #touchPointDataCall;
DROP TABLE IF EXISTS #touchPointDataSignificant;

    SELECT DISTINCT
        sd.seasonYear,
        fctp.dimCustomerMasterId,
        SUM(CASE WHEN touchpointtypename ='Call' and callActivityCount IS NOT NULL THEN callActivityCount ELSE 0 END) AS phonecall
    INTO #touchPointDataCall
    FROM dw.cohortCustomerTouchPoint fctp
        JOIN #seasonDates sd
            ON fctp.callDate >= sd.seasonStartDate
            AND fctp.callDate <= sd.seasonEndDate
    WHERE fctp.lkupClientId = _lkupclientid
    AND callDate IS NOT NULL
    GROUP BY
        sd.seasonYear,
        fctp.dimCustomerMasterId;
       
        SELECT DISTINCT
        sd.seasonYear,
        fctp.dimCustomerMasterId,
        SUM(CASE WHEN touchpointtypename in ('MEETING', 'inPersonContact','appointment','Significant appointment') and callActivityCount IS NOT NULL THEN callActivityCount ELSE 0 END) AS inperson_contact
    INTO #touchPointDataSignificant
    FROM dw.cohortCustomerTouchPoint fctp
        JOIN #seasonDates sd
            ON fctp.significanttpdate >= sd.seasonStartDate
            AND fctp.significanttpdate <= sd.seasonEndDate
    WHERE fctp.lkupClientId = _lkupclientid
    AND significanttpdate IS NOT NULL
    GROUP BY
        sd.seasonYear,
        fctp.dimCustomerMasterId;

	-- END OF CRM

    -- START OF WEB ENGAGEMENT
    DROP TABLE IF EXISTS #WebEngagement;
    SELECT DISTINCT
        sd.seasonYear,
        fctp.dimCustomerMasterId,
        SUM(CASE WHEN activityCount IS NULL THEN 0 ELSE activityCount END) AS WebEngagementActivity
    INTO #WebEngagement
    FROM dw.cohortWebEngagement fctp
        JOIN #seasonDates sd
            ON fctp.activityDate >= sd.seasonStartDate
            AND fctp.activityDate <= sd.seasonEndDate
    WHERE fctp.lkupClientId = _lkupclientid
        AND activityDate IS NOT NULL
    GROUP BY
        sd.seasonYear,
        fctp.dimCustomerMasterId;

	-- END OF WEB ENGAGEMENT

          
    -- live analytics data 
	SELECT DISTINCT 
    fts.dimCustomerMasterId,
        fts.seasonYear,
		ds.gender,
		ds.education, 
		ds.occupation,
		ds.ethnicity,
		ds.maritalStatus, 
		ds.personicXCluster,
		ds.income
	INTO #fscust
	FROM dw.cohortPurchase fts
		INNER JOIN dw.cohortCustomer ds ON fts.dimCustomerMasterId=ds.dimCustomerMasterId
	WHERE fts.lkupClientId = _lkupclientid
		AND fts.isPlanProduct = 1
		AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
		AND fts.isRegularSeason = 1;

	SELECT
		fsc.dimCustomerMasterId,
		fsc.gender, 
        fsc.maritalStatus  AS isMarried,
        CAST(fsc.Income AS char(10) ) AS annualHHIncome,
		fsc.education
	INTO #demoData
	FROM #fscust fsc;

	SELECT dimCustomerMasterId,
		CASE WHEN gender IS NULL THEN 'Unknown' ELSE gender END AS gender,
		CASE WHEN isMarried='0' OR isMarried='Single' THEN 0 ELSE 1 END AS maritalStatus,
		CASE 
			WHEN annualHHIncome='<$15,000' THEN '15000'
			WHEN annualHHIncome='$15,000-$24,999' THEN '24999'
			WHEN annualHHIncome='$25,000-$34,999' THEN '34999'
			WHEN annualHHIncome='$35,000-$59,999' OR annualHHIncome='$35,000 - $59,999' THEN '59999'
			WHEN annualHHIncome='$60,000-$74,999' THEN '74999'
			WHEN annualHHIncome='$75,000-$119,999' THEN '119999'
			WHEN annualHHIncome='$120,000+' THEN '124999'
		ELSE annualHHIncome END AS annualHHIncome,
		education
	INTO #demographicData
	FROM #demoData;
	-- end of live analytics

	SELECT s.seasonYear, MAX(CAST(gameNumber AS int)) NumberofGamesPerSeason 
     INTO #TmpNumberofGamesPerSeason
     FROM dw.dimevent e 
     INNER JOIN dw.dimseason s
     ON e.sourceSeasonId = s.sourceSeasonId
      WHERE e.lkupclientid = _lkupclientid 
      AND isRenewalEvent = 0
      AND isRegularSeason = 1
      AND CAST(s.seasonYear AS int) BETWEEN start_year AND end_year
      GROUP BY s.seasonYear;

     
    DROP TABLE IF EXISTS #customerSeasonProductAgg;

    SELECT dimCustomerMasterId,
            seasonYear,
            productGrouping,
            SUM(fts.ticketCount) numTickets
    INTO #customerSeasonProductAgg
    FROM dw.cohortPurchase fts
	WHERE
		fts.lkupClientId = _lkupclientid
		AND isRegularSeason = 1
		AND isPlanProduct = 1
		AND CAST(fts.seasonYear AS int) BETWEEN start_year AND end_year
    GROUP BY dimCustomerMasterId,productGrouping, seasonYear;

   DROP TABLE IF EXISTS #nextyearbuyer;
  
    SELECT a.dimCustomerMasterId, a.seasonYear, a.productGrouping, COUNT(b.seasonYear) AS isNextYearBuyer
    INTO #nextyearbuyer
    FROM #customerSeasonProductAgg a
        LEFT JOIN #customerSeasonProductAgg b 
        ON a.dimCustomerMasterId = b.dimCustomerMasterId 
        AND (a.seasonYear + 1) = b.seasonYear 
        AND a.productGrouping = b.productGrouping
    GROUP BY a.dimCustomerMasterId, a.seasonYear, a.productGrouping;
  
	-- final select for customer attributes
   
	-- drop table if exists result_retention_scoring; 
	-- create temp table result_retention_scoring as
	OPEN rs_out FOR 
	SELECT DISTINCT 
		sd.lkupClientId,
		sd.dimCustomerMasterId,
		sd.year,
		sd.productGrouping,
		ROUND(sd.totalSpent,2) AS totalSpent ,
		sd.recentDate,
		ROUND(sd.attendancePercent,2) AS attendancePercent,
		sd.renewedBeforeDays,
		sd.source_tenure,
		sd.tenure,
		ROUND(sd.distToVenue,2) AS distToVenue ,
		CASE WHEN a.attended IS NULL OR p.bought IS NULL THEN 0 ELSE p.bought - a.attended END AS recency,
		CASE WHEN mgd.missed_games_1 IS NULL THEN 0 ELSE ROUND(mgd.missed_games_1,2)  END AS missed_games_1,
		CASE WHEN mgd.missed_games_2 IS NULL THEN 0 ELSE ROUND(mgd.missed_games_2,2)  END AS missed_games_2,
		CASE WHEN mgd.missed_games_over_2 IS NULL THEN 0 ELSE ROUND(mgd.missed_games_over_2,2) END AS missed_games_over_2,
		--CASE WHEN md.ClickEmail IS NULL THEN 0 ELSE md.ClickEmail END AS click_link,
		--CASE WHEN md.OpenEmail IS NULL THEN 0 ELSE md.OpenEmail END AS open_email,
		--CASE WHEN md.SendEmail IS NULL THEN 0 ELSE md.SendEmail END AS send_email,
        --CASE WHEN smd.PostingRecords IS NULL THEN 0 ELSE smd.PostingRecords END AS posting_records, 
		--CASE WHEN smd.ResaleRecords IS NULL THEN 0 ELSE smd.ResaleRecords END AS resale_records, 
        CASE WHEN smd.ForwardRecords IS NULL THEN 0 ELSE smd.ForwardRecords END AS forward_records,
		CASE WHEN (md.SendEmail IS NULL OR md.SendEmail = 0 OR md.OpenEmail IS NULL) THEN 0 
		    ELSE ROUND(md.OpenEmail * 1.0/md.SendEmail,2)  END openToSendRatio,
		CASE WHEN (md.SendEmail IS NULL OR md.SendEmail = 0 OR md.ClickEmail IS NULL) THEN 0 
			ELSE ROUND(md.ClickEmail * 1.0/md.SendEmail ,2) 
		END AS clickToSendRatio,
		CASE WHEN (md.OpenEmail IS NULL OR md.OpenEmail = 0 OR md.ClickEmail IS NULL) THEN 0 
			ELSE ROUND(md.ClickEmail * 1.0/md.OpenEmail ,2) 
		END AS clickToOpenRatio,
        CASE WHEN dgd.gender IS NULL THEN 'Unknown' ELSE dgd.gender END AS gender,
        CASE WHEN tpd.phonecall IS NULL THEN 0 ELSE tpd.phonecall END AS phonecall ,
        CASE WHEN tpc.inperson_contact IS NULL THEN 0 ELSE tpc.inperson_contact END AS inperson_contact , 
        cg.isNextYearBuyer AS isNextYear_Buyer
        
	from #scoringData sd
		LEFT JOIN #totalGames tg
			ON sd.dimCustomerMasterId = tg.dimCustomerMasterId
			AND sd.year = tg.seasonYear
			AND sd.productGrouping = tg.productGrouping
		LEFT JOIN #attendance a
			ON sd.dimCustomerMasterId = a.dimCustomerMasterId
			AND sd.year = a.seasonYear
			AND sd.productGrouping = a.productGrouping
		LEFT JOIN #purchase p
			ON sd.dimCustomerMasterId = p.dimCustomerMasterId
			AND sd.year = p.seasonYear
			AND sd.productGrouping = p.productGrouping
		LEFT JOIN #missed_games_data mgd
			ON sd.dimCustomerMasterId = mgd.dimCustomerMasterId
			AND sd.year = mgd.seasonYear
			AND sd.productGrouping = mgd.productGrouping
		LEFT JOIN #marketoData md
			ON sd.dimCustomerMasterId = md.dimCustomerMasterId
			AND sd.year = md.seasonYear
		LEFT JOIN #secondaryData smd
			ON sd.dimCustomerMasterId = smd.dimCustomerMasterId
			AND sd.year = smd.seasonYear
			AND sd.productGrouping = smd.productGrouping
		LEFT JOIN #demographicData dgd
			ON sd.dimCustomerMasterId = dgd.dimCustomerMasterId
        INNER JOIN #nextyearbuyer cg 
        ON cg.dimCustomerMasterId= sd.dimCustomerMasterId
        AND cg.seasonYear= sd.year
        AND cg.productGrouping= sd.productGrouping
        LEFT JOIN #TmpNumberofGamesPerSeason g 
        ON g.seasonYear = sd.year
        LEFT JOIN #WebEngagement w 
        ON sd.dimCustomerMasterId = w.dimCustomerMasterId
		AND sd.year = w.seasonYear 
		LEFT JOIN #touchPointDataCall tpd
		ON tpd.dimCustomerMasterId = sd.dimCustomerMasterId
		AND sd.year = tpd.seasonYear
		LEFT JOIN #touchPointDataSignificant tpc
		ON tpc.dimCustomerMasterId = sd.dimCustomerMasterId
		AND sd.year = tpc.seasonYear
		;
	





END;






$$
;
