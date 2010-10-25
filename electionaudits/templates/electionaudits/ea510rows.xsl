<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:eml="urn:oasis:names:tc:evs:schema:eml"
xmlns:xnl="urn:oasis:names:tc:ciq:xnl:3">
 
 <xsl:template match="/">
  <html>
  <head>
    <title>Election Results: <xsl:value-of select="//eml:Count/eml:EventIdentifier/eml:EventName"/></title>
    <meta HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8"/>
    <style type="text/css">
      td {text-align: right}
    </style>
  </head>
  <body>
   <h1 align="center">Election Results</h1>
   <h2 align="center"><xsl:value-of select="//eml:Count/eml:EventIdentifier/eml:EventName"/></h2>
   <h2 align="center">Election: <xsl:value-of select="//eml:Count/eml:Election/eml:ElectionIdentifier/eml:ElectionName"/></h2>
   <p align="center">Report generated: <xsl:value-of select="//eml:IssueDate"/></p>

   <table align="center" border='1' cellpadding='2' cellspacing='0'>
     <tr bgcolor="#9acd32">
       <th>Batch Seq</th>
       <th>Batches</th>
       <th>Type</th>
       <th>Ballots</th>
       <th>Contest Ballots</th>
       <xsl:for-each select="//eml:Election/eml:Contests/eml:Contest/eml:TotalVotes/eml:Selection/eml:Candidate">
	 <th style="writing-mode: tb-rl;"><xsl:value-of select="eml:CandidateIdentifier/eml:CandidateName" />
	   <xsl:value-of select="eml:ProposalItem/@ProposalIdentifier" />
	 </th>
       </xsl:for-each>
     </tr>

     <tr>
       <td>Totals</td>
     </tr>

     <xsl:for-each select="//eml:Election/eml:Contests/eml:Contest/eml:ReportingUnitVotes">

       <tr>
	 <th/> <!-- increment for each batch -->
	 <th><xsl:value-of select="eml:ReportingUnitIdentifier"/></th>
	 <th/> <!-- type -->
	 <th/> <!-- ballots -->
	 <th/> <!-- contest ballots -->

	 <xsl:for-each select="eml:Selection">
	   <xsl:if test="eml:ValidVotes &gt; 0">
             <td><xsl:value-of select="eml:ValidVotes" /></td>
	   </xsl:if>
	   <xsl:if test="eml:ValidVotes &lt; 1">
             <td></td>
	   </xsl:if>
	 </xsl:for-each>
       </tr>
     </xsl:for-each>
   </table>

<!--
       <xsl:if test="eml:CountMetric[1]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[1]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[1]" /></td>
       </tr>
         </xsl:if>
-->

  <p align="center">
   <a href="https://launchpad.net/electionaudits">
   ElectionAudits Home Page (generator of this EML report)</a>
  </p>
  </body>
  </html>
</xsl:template></xsl:stylesheet>
