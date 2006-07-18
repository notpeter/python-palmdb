XSLT_GanttProject_ToDesktop=\
'''
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:template match="palmDatabase">
<project name="Untitled Gantt Project" company="" webLink="http://" view-date="2006-07-18" view-index="0" gantt-divider-location="316" resource-divider-location="-1" version="2.0">
<description></description>
<tasks color="#8cb6ce">
<taskproperties>
<taskproperty id="tpd0" name="type" type="default" valuetype="icon"/>
<taskproperty id="tpd1" name="priority" type="default" valuetype="icon"/>
<taskproperty id="tpd2" name="info" type="default" valuetype="icon"/>
<taskproperty id="tpd3" name="name" type="default" valuetype="text"/>
<taskproperty id="tpd4" name="begindate" type="default" valuetype="date"/>
<taskproperty id="tpd5" name="enddate" type="default" valuetype="date"/>
<taskproperty id="tpd6" name="duration" type="default" valuetype="int"/>
<taskproperty id="tpd7" name="completion" type="default" valuetype="int"/>
<taskproperty id="tpd8" name="coordinator" type="default" valuetype="text"/>
<taskproperty id="tpd9" name="predecessorsr" type="default" valuetype="text"/>
</taskproperties>
<xsl:apply-templates select="ProgectDataRecord"/>
</tasks>
</project>
</xsl:template>

<xsl:template match="ProgectDataRecord">
<task
id="{recordAttributes/attribute[@name='uid']/*/@value}"
name="{recordAttributes/attribute[@name='description']/*/@value}"
expand="{recordAttributes/attribute[@name='opened']/*/@value}"
>
<xsl:if test="recordAttributes/attribute[@name='dueDate']">
<xsl:attribute name="duration"><xsl:text>1</xsl:text></xsl:attribute>
<xsl:attribute name="start">
<xsl:value-of select="recordAttributes/attribute[@name='dueDate']/*/@year"/>-<xsl:value-of select="recordAttributes/attribute[@name='dueDate']/*/@month"/>-<xsl:value-of select="recordAttributes/attribute[@name='dueDate']/*/@day"/>
</xsl:attribute>
</xsl:if>
<notes><xsl:value-of select="recordAttributes/attribute[@name='note']/*/@value"/></notes>
<xsl:apply-templates select="children/ProgectDataRecord"/>
</task>
</xsl:template>

<!--
<xsl:template name="dueDate" match="ProgectDataRecord">
<xsl:attribute name="splat"/>
<xsl:attribute name="duration"><xsl:text>1</xsl:text></xsl:attribute>
<xsl:attribute name="start">
<xsl:value-of select="recordAttributes/attribute[@name='year']/*/@value"/>-
<xsl:value-of select="recordAttributes/attribute[@name='month']/*/@value"/>-
<xsl:value-of select="recordAttributes/attribute[@name='day']/*/@value"/>
</xsl:attribute>
</xsl:template>
-->

<!--
<xsl:template match="@*|node()">
<xsl:copy>
<xsl:apply-templates select="@*|node()"/>
</xsl:copy>
</xsl:template>
<xsl:template match="@id"/>
-->
</xsl:stylesheet>
'''

XSLT_GanttProject_FromDesktop=\
'''
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:template match="@*|node()">
<xsl:copy>
<xsl:apply-templates select="@*|node()"/>
</xsl:copy>
</xsl:template>
<xsl:template match="@id"/>
</xsl:stylesheet>
'''
