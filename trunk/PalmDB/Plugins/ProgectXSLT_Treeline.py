XSLT_Treeline_ToDesktop=\
'''
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:template match="palmDatabase">
<ROOT item="y" tlversion="1.0.0" line0="{Name}" line1="{Name}" childtype="DEFAULT">
<Name type="Text" ref="y">Should replace with project name?Main</Name>
<xsl:apply-templates select="ProgectDataRecord"/>
</ROOT>
</xsl:template>

<xsl:template match="ProgectDataRecord">
<xsl:element name="{recordAttributes/attribute[@name='description']/*/@value"}></xsl:element>
<DEFAULT item="y" line0="{Name}" line1="{Name}">
<Name type="Text" ref="y"><xsl:value-of select="recordAttributes/attribute[@name='description']/*/@value"/></Name>
<xsl:apply-templates select="children/ProgectDataRecord"/>
</DEFAULT>
</xsl:template>

</xsl:stylesheet>
'''

XSLT_Treeline_FromDesktop=\
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
