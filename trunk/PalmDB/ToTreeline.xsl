<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:output indent="yes"/> 

<xsl:template match="palmDatabase">
<ROOT item="y" tlversion="1.0.0" childtype="DEFAULT">
<xsl:attribute name="line0">{*Name*}</xsl:attribute>
<xsl:attribute name="line1">{*Name*}</xsl:attribute>
<Name type="Text" ref="y">Should replace with project name?Main</Name>
<xsl:apply-templates select="ProgectDataRecord"/>
</ROOT>
</xsl:template>

<xsl:template match="ProgectDataRecord">
<xsl:element name="{recordAttributes/attribute[@name='itemType']/*/@value}">
<xsl:attribute name="line0">{*description*}</xsl:attribute>
<xsl:attribute name="line1">{*description*}</xsl:attribute>
<xsl:attribute name="item">y</xsl:attribute>

<xsl:apply-templates select="recordAttributes"/>

<xsl:apply-templates select="children/ProgectDataRecord"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[string]">
<xsl:element name="{@name}">
<xsl:attribute name="type">Text</xsl:attribute>
<xsl:apply-templates select="*"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[@name='itemType'][string]">
<xsl:element name="{@name}">
<xsl:attribute name="type">Choice</xsl:attribute>
<xsl:attribute name="format">Progress/Numeric/Action/Info</xsl:attribute>
<xsl:apply-templates select="*"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[@name='priority']">
<xsl:element name="{@name}">
<xsl:attribute name="type">Choice</xsl:attribute>
<xsl:attribute name="format">1/2/3/4/5/None</xsl:attribute>
<xsl:apply-templates select="*"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[boolean]">
<xsl:element name="{@name}">
<xsl:attribute name="type">Boolean</xsl:attribute>
<xsl:attribute name="format">yes/no</xsl:attribute>
<xsl:if test="@name='busy' or @name='opened' or @name='deleted' or @name='hasToDo' or @name='dirty'">
<xsl:attribute name="hidden">y</xsl:attribute>
</xsl:if>
<xsl:apply-templates select="*"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[integer]">
<xsl:element name="{@name}">
<xsl:attribute name="type">Number</xsl:attribute>
<xsl:attribute name="format">##########</xsl:attribute>
<xsl:if test="@name='uid' or @name='icon' ">
<xsl:attribute name="hidden">y</xsl:attribute>
</xsl:if>
<xsl:apply-templates select="*"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[rational]">
<xsl:element name="{@name}">
<xsl:attribute name="type">Text</xsl:attribute>
<xsl:apply-templates select="*"/>
</xsl:element>
</xsl:template>

<xsl:template match="attribute[date]">
<xsl:element name="{@name}">
<xsl:attribute name="type">Date</xsl:attribute>
<xsl:attribute name="format">yyyy/mm/dd</xsl:attribute>
<xsl:apply-templates select="*"/>
</xsl:element>

</xsl:template>
<xsl:template match="string|boolean|integer">
<xsl:value-of select="@value"/>
</xsl:template>

<xsl:template match="rational">
<xsl:value-of select="@numerator"/>/<xsl:value-of select="@denominator"/>
</xsl:template>

<xsl:template match="date">
<xsl:value-of select="@year"/>/<xsl:value-of select="@month"/>/<xsl:value-of select="@day"/>
</xsl:template>



</xsl:stylesheet>
