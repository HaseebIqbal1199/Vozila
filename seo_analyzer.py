#!/usr/bin/env python3
"""
SEO Analysis Tool for YouTube Downloader
Run this script to analyze your deployed site's SEO performance
"""

import requests
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

class SEOAnalyzer:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_page(self, path='/'):
        """Analyze SEO for a specific page"""
        url = urljoin(self.base_url, path)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return {'error': f'Failed to fetch {url}: {str(e)}'}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        analysis = {
            'url': url,
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds(),
            'content_length': len(response.content),
            'title': self._get_title(soup),
            'meta_description': self._get_meta_description(soup),
            'meta_keywords': self._get_meta_keywords(soup),
            'h1_tags': self._get_h1_tags(soup),
            'h2_tags': self._get_h2_tags(soup),
            'images': self._analyze_images(soup),
            'links': self._analyze_links(soup),
            'open_graph': self._get_open_graph(soup),
            'twitter_cards': self._get_twitter_cards(soup),
            'structured_data': self._get_structured_data(soup),
            'canonical': self._get_canonical(soup),
            'robots_meta': self._get_robots_meta(soup),
            'lang': self._get_lang(soup)
        }
        
        # Add SEO score
        analysis['seo_score'] = self._calculate_seo_score(analysis)
        
        return analysis
    
    def _get_title(self, soup):
        title_tag = soup.find('title')
        return {
            'text': title_tag.get_text().strip() if title_tag else None,
            'length': len(title_tag.get_text().strip()) if title_tag else 0,
            'optimal': 30 <= len(title_tag.get_text().strip()) <= 60 if title_tag else False
        }
    
    def _get_meta_description(self, soup):
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '').strip()
            return {
                'text': content,
                'length': len(content),
                'optimal': 120 <= len(content) <= 160
            }
        return {'text': None, 'length': 0, 'optimal': False}
    
    def _get_meta_keywords(self, soup):
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        return meta_keywords.get('content', '').strip() if meta_keywords else None
    
    def _get_h1_tags(self, soup):
        h1_tags = soup.find_all('h1')
        return {
            'count': len(h1_tags),
            'texts': [h1.get_text().strip() for h1 in h1_tags],
            'optimal': len(h1_tags) == 1
        }
    
    def _get_h2_tags(self, soup):
        h2_tags = soup.find_all('h2')
        return {
            'count': len(h2_tags),
            'texts': [h2.get_text().strip() for h2 in h2_tags]
        }
    
    def _analyze_images(self, soup):
        images = soup.find_all('img')
        missing_alt = sum(1 for img in images if not img.get('alt'))
        
        return {
            'total': len(images),
            'missing_alt': missing_alt,
            'alt_coverage': (len(images) - missing_alt) / len(images) * 100 if images else 100
        }
    
    def _analyze_links(self, soup):
        links = soup.find_all('a', href=True)
        internal_links = []
        external_links = []
        
        for link in links:
            href = link['href']
            if href.startswith('http'):
                if urlparse(href).netloc == urlparse(self.base_url).netloc:
                    internal_links.append(href)
                else:
                    external_links.append(href)
            elif href.startswith('/') or href.startswith('#'):
                internal_links.append(href)
        
        return {
            'total': len(links),
            'internal': len(internal_links),
            'external': len(external_links)
        }
    
    def _get_open_graph(self, soup):
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        return {tag.get('property'): tag.get('content') for tag in og_tags}
    
    def _get_twitter_cards(self, soup):
        twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
        return {tag.get('name'): tag.get('content') for tag in twitter_tags}
    
    def _get_structured_data(self, soup):
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        structured_data = []
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except json.JSONDecodeError:
                continue
        
        return structured_data
    
    def _get_canonical(self, soup):
        canonical = soup.find('link', rel='canonical')
        return canonical.get('href') if canonical else None
    
    def _get_robots_meta(self, soup):
        robots = soup.find('meta', attrs={'name': 'robots'})
        return robots.get('content') if robots else None
    
    def _get_lang(self, soup):
        html_tag = soup.find('html')
        return html_tag.get('lang') if html_tag else None
    
    def _calculate_seo_score(self, analysis):
        """Calculate SEO score based on various factors"""
        score = 0
        max_score = 100
        
        # Title optimization (20 points)
        if analysis['title']['optimal']:
            score += 20
        elif analysis['title']['text']:
            score += 10
        
        # Meta description (15 points)
        if analysis['meta_description']['optimal']:
            score += 15
        elif analysis['meta_description']['text']:
            score += 8
        
        # H1 tags (15 points)
        if analysis['h1_tags']['optimal']:
            score += 15
        elif analysis['h1_tags']['count'] > 0:
            score += 8
        
        # Images with alt text (10 points)
        if analysis['images']['alt_coverage'] == 100:
            score += 10
        elif analysis['images']['alt_coverage'] >= 80:
            score += 7
        
        # Open Graph (10 points)
        if len(analysis['open_graph']) >= 5:
            score += 10
        elif len(analysis['open_graph']) > 0:
            score += 5
        
        # Structured data (10 points)
        if len(analysis['structured_data']) > 0:
            score += 10
        
        # Canonical URL (5 points)
        if analysis['canonical']:
            score += 5
        
        # Language declaration (5 points)
        if analysis['lang']:
            score += 5
        
        # Response time (10 points)
        if analysis['response_time'] < 2:
            score += 10
        elif analysis['response_time'] < 5:
            score += 5
        
        return min(score, max_score)
    
    def check_technical_seo(self):
        """Check technical SEO aspects"""
        results = {}
        
        # Check robots.txt
        try:
            robots_response = self.session.get(f"{self.base_url}/robots.txt", timeout=10)
            results['robots_txt'] = {
                'exists': robots_response.status_code == 200,
                'content': robots_response.text[:500] if robots_response.status_code == 200 else None
            }
        except:
            results['robots_txt'] = {'exists': False, 'content': None}
        
        # Check sitemap.xml
        try:
            sitemap_response = self.session.get(f"{self.base_url}/sitemap.xml", timeout=10)
            results['sitemap_xml'] = {
                'exists': sitemap_response.status_code == 200,
                'valid': sitemap_response.status_code == 200 and 'xml' in sitemap_response.headers.get('content-type', '')
            }
        except:
            results['sitemap_xml'] = {'exists': False, 'valid': False}
        
        # Check HTTPS
        results['https'] = {
            'enabled': self.base_url.startswith('https://'),
            'redirects_http': self._check_http_redirect()
        }
        
        return results
    
    def _check_http_redirect(self):
        """Check if HTTP redirects to HTTPS"""
        if not self.base_url.startswith('https://'):
            return False
        
        http_url = self.base_url.replace('https://', 'http://')
        try:
            response = self.session.get(http_url, allow_redirects=False, timeout=10)
            return response.status_code in [301, 302] and 'https' in response.headers.get('location', '')
        except:
            return False
    
    def generate_report(self):
        """Generate complete SEO report"""
        print(f"🔍 SEO Analysis Report for {self.base_url}")
        print("=" * 60)
        
        # Analyze main page
        homepage_analysis = self.analyze_page('/')
        
        if 'error' in homepage_analysis:
            print(f"❌ Error: {homepage_analysis['error']}")
            return
        
        print(f"📊 Overall SEO Score: {homepage_analysis['seo_score']}/100")
        print()
        
        # Title analysis
        title = homepage_analysis['title']
        print(f"📝 Title: {title['text'][:50]}..." if len(title['text']) > 50 else f"📝 Title: {title['text']}")
        print(f"   Length: {title['length']} characters {'✅' if title['optimal'] else '⚠️'}")
        print()
        
        # Meta description
        meta_desc = homepage_analysis['meta_description']
        if meta_desc['text']:
            print(f"📄 Meta Description: {meta_desc['text'][:50]}...")
            print(f"   Length: {meta_desc['length']} characters {'✅' if meta_desc['optimal'] else '⚠️'}")
        else:
            print("📄 Meta Description: ❌ Missing")
        print()
        
        # Headers
        h1 = homepage_analysis['h1_tags']
        print(f"🏷️  H1 Tags: {h1['count']} {'✅' if h1['optimal'] else '⚠️'}")
        if h1['texts']:
            for i, text in enumerate(h1['texts'][:3]):
                print(f"   {i+1}. {text[:50]}..." if len(text) > 50 else f"   {i+1}. {text}")
        print()
        
        # Images
        images = homepage_analysis['images']
        print(f"🖼️  Images: {images['total']} total, {images['missing_alt']} missing alt text")
        print(f"   Alt coverage: {images['alt_coverage']:.1f}% {'✅' if images['alt_coverage'] == 100 else '⚠️'}")
        print()
        
        # Technical SEO
        print("🔧 Technical SEO:")
        technical = self.check_technical_seo()
        
        robots = technical['robots_txt']
        print(f"   robots.txt: {'✅' if robots['exists'] else '❌'}")
        
        sitemap = technical['sitemap_xml']
        print(f"   sitemap.xml: {'✅' if sitemap['exists'] and sitemap['valid'] else '❌'}")
        
        https = technical['https']
        print(f"   HTTPS: {'✅' if https['enabled'] else '❌'}")
        print(f"   HTTP→HTTPS redirect: {'✅' if https['redirects_http'] else '❌'}")
        print()
        
        # Performance
        print(f"⚡ Performance:")
        print(f"   Response time: {homepage_analysis['response_time']:.2f}s {'✅' if homepage_analysis['response_time'] < 3 else '⚠️'}")
        print(f"   Page size: {homepage_analysis['content_length']/1024:.1f} KB")
        print()
        
        # Structured data
        structured_data = homepage_analysis['structured_data']
        print(f"📊 Structured Data: {len(structured_data)} schemas found {'✅' if structured_data else '⚠️'}")
        for data in structured_data:
            if isinstance(data, dict) and '@type' in data:
                print(f"   - {data['@type']}")
        print()
        
        # Recommendations
        self._print_recommendations(homepage_analysis, technical)
    
    def _print_recommendations(self, analysis, technical):
        """Print SEO recommendations"""
        recommendations = []
        
        if not analysis['title']['optimal']:
            if analysis['title']['length'] < 30:
                recommendations.append("📝 Title is too short - aim for 30-60 characters")
            elif analysis['title']['length'] > 60:
                recommendations.append("📝 Title is too long - aim for 30-60 characters")
        
        if not analysis['meta_description']['optimal']:
            if not analysis['meta_description']['text']:
                recommendations.append("📄 Add a meta description (120-160 characters)")
            elif analysis['meta_description']['length'] < 120:
                recommendations.append("📄 Meta description is too short - aim for 120-160 characters")
            elif analysis['meta_description']['length'] > 160:
                recommendations.append("📄 Meta description is too long - aim for 120-160 characters")
        
        if not analysis['h1_tags']['optimal']:
            if analysis['h1_tags']['count'] == 0:
                recommendations.append("🏷️ Add exactly one H1 tag to your page")
            elif analysis['h1_tags']['count'] > 1:
                recommendations.append("🏷️ Use only one H1 tag per page")
        
        if analysis['images']['alt_coverage'] < 100:
            recommendations.append("🖼️ Add alt text to all images for better accessibility and SEO")
        
        if not technical['robots_txt']['exists']:
            recommendations.append("🤖 Create a robots.txt file")
        
        if not technical['sitemap_xml']['exists']:
            recommendations.append("🗺️ Create and submit a sitemap.xml file")
        
        if not technical['https']['enabled']:
            recommendations.append("🔒 Enable HTTPS for better security and SEO")
        
        if analysis['response_time'] > 3:
            recommendations.append("⚡ Improve page load speed (currently {:.2f}s)".format(analysis['response_time']))
        
        if len(analysis['structured_data']) == 0:
            recommendations.append("📊 Add structured data markup for better search results")
        
        if recommendations:
            print("💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("🎉 Great job! No major SEO issues found.")

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python seo_analyzer.py <website_url>")
        print("Example: python seo_analyzer.py https://ytdownloader.pro")
        sys.exit(1)
    
    url = sys.argv[1]
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    analyzer = SEOAnalyzer(url)
    analyzer.generate_report()

if __name__ == '__main__':
    main()
