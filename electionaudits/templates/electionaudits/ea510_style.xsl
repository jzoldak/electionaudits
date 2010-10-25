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
     th {FONT-FAMILY:Arial; font-size:10pt}
     td {FONT-FAMILY:Arial; font-size:10pt}
    </style>
  </head>
  <body>
   <h1 align="center">Election Results</h1>
   <h2 align="center"><xsl:value-of select="//eml:Count/eml:EventIdentifier/eml:EventName"/></h2>
   <h2 align="center">Election: <xsl:value-of select="//eml:Count/eml:Election/eml:ElectionIdentifier/eml:ElectionName"/></h2>
   <p align="center">Report generated: <xsl:value-of select="//eml:IssueDate"/></p>

   <table align="center" style="border-collapse: collapse" border='1' width='700' cellpadding='2' cellspacing='0'>
      <tr bgcolor="#9acd32">
        <th align="left" width="50%">Ballot</th>
        <th align="left" width="30%">Metric</th>
        <th align="left" width="20%">Total</th>
      </tr>

   <xsl:for-each select="//eml:Election/eml:Contests/eml:Contest">

      <tr bgcolor="#dddddd">
        <th align="left" width="50%"><font size="4" color="#cc3333"><xsl:value-of select="eml:ContestIdentifier/eml:ContestName" /></font></th>
        <th align="center" width="30%"><font size="2" color="#666666">ContestID = <xsl:value-of select="eml:ContestIdentifier/@IdNumber" /></font></th>
        <th align="left" width="20%"></th>
      </tr>
      
      
      
  
      
     <xsl:for-each select="eml:TotalVotes">

      <tr bgcolor="#ccffcc">
        <th align="left" width="50%">Totals</th>
        <th align="left" width="30%"></th>
        <th align="right" width="20%"></th>
      </tr>

       <xsl:if test="eml:CountMetric[1]/@Type">
      <tr bgcolor="#ffffcc">
        <th align="left" width="50%"></th>
        <th align="left" width="30%"><xsl:value-of select="eml:CountMetric[1]/@Type" /></th>
        <th align="right" width="20%"><xsl:value-of select="eml:CountMetric[1]" /></th>
      </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[2]/@Type">
      <tr bgcolor="#ffffcc">
        <th align="left" width="50%"></th>
        <th align="left" width="30%"><xsl:value-of select="eml:CountMetric[2]/@Type" /></th>
        <th align="right" width="20%"><xsl:value-of select="eml:CountMetric[2]" /></th>
      </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[3]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[3]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[3]" /></td>
       </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[4]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[4]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[4]" /></td>
       </tr>
       </xsl:if>

      <xsl:for-each select="eml:Selection">
       <tr bgcolor="#eeeeff">
        <td align="left" width="50%">
        <xsl:value-of select="eml:Candidate/eml:CandidateIdentifier/eml:CandidateName" />
        <xsl:value-of select="eml:Candidate/eml:ProposalItem/@ProposalIdentifier" />
        
        <xsl:if test="eml:AffiliationIdentifier/@IdNumber">
        [<font color='red'><xsl:value-of select="eml:AffiliationIdentifier/@IdNumber" /></font>]
         </xsl:if>

        <xsl:if test="eml:Candidate/eml:Affiliation[1]/eml:Type">
        [<font color='green'>Party=<xsl:value-of select="eml:Candidate/eml:Affiliation[1]/eml:Type" /></font>]
         </xsl:if>

        </td>
        
        <td align="left" width="30%"><xsl:value-of select="eml:Candidate/eml:ProposalItem/@ReferendumOptionIdentifier"/></td>
         <xsl:if test="eml:ValidVotes &gt; 0">
          <td align="right" width="20%"><b><xsl:value-of select="eml:ValidVotes" /></b></td>
         </xsl:if>
         <xsl:if test="eml:ValidVotes &lt; 1">
          <td align="right" width="20%"> </td>
         </xsl:if>
       </tr>

       <xsl:if test="eml:CountMetric[1]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[1]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[1]" /></td>
       </tr>
         </xsl:if>

       <xsl:if test="eml:CountMetric[2]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[2]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[2]" /></td>
       </tr>
         </xsl:if>

      </xsl:for-each>
     </xsl:for-each>     
      
    
      
      
      
 <xsl:for-each select="eml:ReportingUnitVotes">

       <xsl:if test="eml:ReportingUnitIdentifier">
      <tr bgcolor="#ccffcc">
        <th align="left" width="50%">Batch <xsl:value-of select="eml:ReportingUnitIdentifier" /></th>
        <th align="left" width="30%"></th>
        <th align="right" width="20%"></th>
      </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[1]/@Type">
      <tr bgcolor="#ffffcc">
        <th align="left" width="50%"></th>
        <th align="left" width="30%"><xsl:value-of select="eml:CountMetric[1]/@Type" /></th>
        <th align="right" width="20%"><xsl:value-of select="eml:CountMetric[1]" /></th>
      </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[2]/@Type">
      <tr bgcolor="#ffffcc">
        <th align="left" width="50%"></th>
        <th align="left" width="30%"><xsl:value-of select="eml:CountMetric[2]/@Type" /></th>
        <th align="right" width="20%"><xsl:value-of select="eml:CountMetric[2]" /></th>
      </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[3]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[3]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[3]" /></td>
       </tr>
       </xsl:if>

       <xsl:if test="eml:CountMetric[4]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[4]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[4]" /></td>
       </tr>
       </xsl:if>

      <xsl:for-each select="eml:Selection">
       <tr bgcolor="#eeeeff">
        <td align="left" width="50%"><xsl:value-of select="eml:Candidate/eml:CandidateIdentifier/eml:CandidateName" />
        <xsl:value-of select="eml:Candidate/eml:ProposalItem/@ProposalIdentifier" />
        
        <xsl:if test="eml:AffiliationIdentifier/@IdNumber">
        [<font color='red'><xsl:value-of select="eml:AffiliationIdentifier/@IdNumber" /></font>]
         </xsl:if>

        <xsl:if test="eml:Candidate/eml:Affiliation[1]/eml:Type">
        [<font color='green'>Party=<xsl:value-of select="eml:Candidate/eml:Affiliation[1]/eml:Type" /></font>]
         </xsl:if>
        
        </td>
        <td align="left" width="30%"><xsl:value-of select="eml:Candidate/eml:ProposalItem/@ReferendumOptionIdentifier"/></td>
         <xsl:if test="eml:ValidVotes &gt; 0">
          <td align="right" width="30%"><b><xsl:value-of select="eml:ValidVotes" /></b></td>
         </xsl:if>
         <xsl:if test="eml:ValidVotes &lt; 1">
          <td align="right" width="20%"> </td>
         </xsl:if>
       </tr>

       <xsl:if test="eml:CountMetric[1]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[1]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[1]" /></td>
       </tr>
         </xsl:if>

       <xsl:if test="eml:CountMetric[2]/@Type">
       <tr>
        <td align="left" width="50%"></td>
        <td align="left" width="30%"><xsl:value-of select="eml:CountMetric[2]/@Type" /></td>
        <td align="right" width="20%"><xsl:value-of select="eml:CountMetric[2]" /></td>
       </tr>
         </xsl:if>

      </xsl:for-each>
      

<!--
      <tr>
        <th align="left" width="40%"><hr/></th>
        <th align="left" width="40%"><hr/></th>
        <th align="left" width="20%"><hr/></th>
      </tr>
-->      
      </xsl:for-each>
  </xsl:for-each>

  </table>

  <p align="center">
   <a href="https://launchpad.net/electionaudits">
   ElectionAudits Home Page (generator of this EML report)</a>
  </p>
  </body>
  </html>
</xsl:template></xsl:stylesheet>
