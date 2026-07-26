from datetime import date

SITEMAP = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://streamzeast.click/</loc>
    <lastmod>{}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
'''

with open('sitemap.xml', 'w') as f:
    f.write(SITEMAP.format(date.today().isoformat()))
