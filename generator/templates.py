atom_template = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title type="text">issarice.com</title>
  <updated>{now}</updated>
  <author>
    <name>Issa Rice</name>
  </author>
  <id>http://issarice.com/</id>
  <link href="http://issarice.com/atom.xml" rel="self" type="application/atom+xml" />
  <link rel="alternate" type="application/rss+xml" hreflang="en" href="http://issarice.com/rss.xml" />
  <generator uri="https://github.com/riceissa/issarice.com/blob/master/generator/generator.py">generator.py</generator>
{inner_list}
</feed>
"""

atom_list = """    <entry>
      <title>{title}</title>
      <link href="http://issarice.com/{slug}"/>
      <id>tag:issarice.com,{date}:/{slug}</id>
      <updated>{datetime}</updated>
    </entry>
"""
