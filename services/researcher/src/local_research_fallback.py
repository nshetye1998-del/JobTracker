"""
Local Research Fallback System
===============================
Intelligent research fallback using historical data.

5-Level Fallback Strategy:
1. Exact match (same company + role) - 95% quality
2. Same company (different role) - 85% quality  
3. Same role (different company) - 75% quality
4. Industry patterns - 60% quality
5. Generic template - 40% quality
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class LocalResearchFallback:
    """
    Intelligent research fallback using historical data.
    Gets smarter over time and never fails.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        logger.info("✅ Local research fallback initialized")
    
    def save_research(self, company: str, role: str, research_data: Dict, source: str):
        """Save successful research to cache for future use"""
        
        cursor = self.db.cursor()
        company_norm = self._normalize(company)
        role_norm = self._normalize(role)
        
        try:
            # Extract description from research_data
            description = ""
            if isinstance(research_data, dict):
                description = research_data.get('description', '') or research_data.get('company_info', '')
                if isinstance(description, dict):
                    description = str(description)
            
            cursor.execute("""
            INSERT INTO research_cache (
                company, role, description, data_source, research_quality,
                company_normalized, role_normalized, researched_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (company_normalized, role_normalized) 
            DO UPDATE SET
                description = EXCLUDED.description,
                data_source = EXCLUDED.data_source,
                researched_at = NOW()
            """, (
                company,
                role or "General",
                description[:5000],  # Limit size
                source,
                0.85,  # Default quality score
                company_norm,
                role_norm
            ))
            self.db.commit()
            logger.info(f"💾 Cached research: {company} - {role} (source: {source})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cache research: {e}")
            self.db.rollback()
            return False
    
    def generate_fallback_research(self, company: str, role: str) -> Dict:
        """
        Generate intelligent fallback using 5-level strategy
        """
        
        company_norm = self._normalize(company)
        role_norm = self._normalize(role or "")
        
        logger.info(f"🔍 Generating fallback research for {company} - {role}")
        
        # LEVEL 1: Exact match (best quality)
        exact = self._find_exact_match(company_norm, role_norm)
        if exact:
            logger.info(f"✅ Level 1: Exact match found!")
            return self._format_exact_match(exact, company, role)
        
        # LEVEL 2: Same company, different role
        same_company = self._find_same_company(company_norm)
        if same_company:
            logger.info(f"✅ Level 2: Same company found ({same_company['role']})")
            return self._format_same_company(same_company, company, role)
        
        # LEVEL 3: Same role, different companies
        if role_norm:
            same_role = self._find_same_role(role_norm)
            if same_role:
                logger.info(f"✅ Level 3: Found {len(same_role)} similar roles")
                return self._format_same_role(same_role, company, role)
        
        # LEVEL 4: Industry patterns
        if role_norm:
            patterns = self._find_patterns(role_norm)
            if patterns and patterns['count'] > 0:
                logger.info(f"✅ Level 4: Found {patterns['count']} industry patterns")
                return self._format_patterns(patterns, company, role)
        
        # LEVEL 5: Generic template (last resort)
        logger.info(f"⚠️ Level 5: No history, using generic template")
        return self._format_generic(company, role)
    
    def _find_exact_match(self, company_norm: str, role_norm: str) -> Optional[Dict]:
        """Level 1: Find exact company + role match"""
        cursor = self.db.cursor()
        cursor.execute("""
        SELECT company, role, description, data_source, researched_at
        FROM research_cache
        WHERE company_normalized = %s AND role_normalized = %s
        ORDER BY researched_at DESC LIMIT 1
        """, (company_norm, role_norm))
        
        row = cursor.fetchone()
        if row:
            return {
                'company': row[0],
                'role': row[1],
                'description': row[2],
                'source': row[3],
                'date': row[4]
            }
        return None
    
    def _find_same_company(self, company_norm: str) -> Optional[Dict]:
        """Level 2: Find same company, any role"""
        cursor = self.db.cursor()
        cursor.execute("""
        SELECT company, role, description, data_source, researched_at
        FROM research_cache
        WHERE company_normalized = %s
        ORDER BY researched_at DESC LIMIT 1
        """, (company_norm,))
        
        row = cursor.fetchone()
        if row:
            return {
                'company': row[0],
                'role': row[1],
                'description': row[2],
                'source': row[3],
                'date': row[4]
            }
        return None
    
    def _find_same_role(self, role_norm: str) -> Optional[List[Dict]]:
        """Level 3: Find same role at other companies"""
        cursor = self.db.cursor()
        cursor.execute("""
        SELECT company, role, description, data_source
        FROM research_cache
        WHERE role_normalized = %s
        ORDER BY researched_at DESC LIMIT 5
        """, (role_norm,))
        
        rows = cursor.fetchall()
        if rows:
            return [{
                'company': r[0],
                'role': r[1],
                'description': r[2],
                'source': r[3]
            } for r in rows]
        return None
    
    def _find_patterns(self, role_norm: str) -> Optional[Dict]:
        """Level 4: Find industry patterns"""
        cursor = self.db.cursor()
        
        # Use first 8 characters for pattern matching
        pattern = role_norm[:8] if len(role_norm) >= 8 else role_norm
        
        cursor.execute("""
        SELECT COUNT(*) as count, 
               STRING_AGG(DISTINCT company, ', ') as companies
        FROM research_cache
        WHERE role_normalized LIKE %s
        """, (f'%{pattern}%',))
        
        row = cursor.fetchone()
        if row and row[0] > 0:
            return {'count': row[0], 'companies': row[1]}
        return None
    
    def _format_exact_match(self, cached: Dict, company: str, role: str) -> Dict:
        """Format Level 1: Exact match"""
        days_old = (datetime.now() - cached['date']).days
        
        description = f"""📋 {company} - {role}

{cached['description']}

📊 Data Quality: Exact match from cache
🗓️ Research Date: {days_old} days ago
🔍 Original Source: {cached['source']}

Note: Core company information remains accurate. Some details may have changed since research date."""
        
        return {
            "success": True,
            "provider": "local_cache",
            "match_type": "exact_match",
            "company_info": {
                "company": company,
                "role": role,
                "description": description.strip(),
                "data_age_days": days_old,
                "cached": True,
                "quality": 0.95
            },
            "response_time_ms": 1
        }
    
    def _format_same_company(self, cached: Dict, company: str, role: str) -> Dict:
        """Format Level 2: Same company"""
        
        # Extract core content from cached description (remove header and footer)
        cached_desc = cached['description']
        
        # Strip the emoji header line if it exists (e.g., "📋 Company - Role")
        lines = cached_desc.split('\n')
        core_content_lines = []
        skip_mode = True
        
        for line in lines:
            # Skip header lines (emoji-based or "Based on" lines)
            if line.strip().startswith('📋') or line.strip().startswith('Based on our research'):
                skip_mode = True
                continue
            # Skip footer metadata lines (📊, 🔍, 🔄, Note:)
            if any(line.strip().startswith(marker) for marker in ['📊', '🔍', '🔄', 'Note:']):
                skip_mode = True
                continue
            # Skip empty lines at the start
            if skip_mode and not line.strip():
                continue
            # Start capturing content
            skip_mode = False
            core_content_lines.append(line)
        
        # Join the core content and trim
        core_content = '\n'.join(core_content_lines).strip()
        
        # If we couldn't extract core content, use a safe fallback
        if not core_content or len(core_content) < 50:
            core_content = f"Company information based on our research for {cached['role']} role at {company}. Role details have been adapted for {role}."
        
        description = f"""📋 {company} - {role}

Based on our research about {company} (originally researched for {cached['role']} role):

{core_content}

📊 Adaptation: Company info is accurate, role details are generic
🔍 Original Research: {cached['role']} at {company}
🔄 Adapted for: {role}

Note: Company culture, benefits, and interview process typically similar across roles."""
        
        return {
            "success": True,
            "provider": "local_cache",
            "match_type": "same_company",
            "company_info": {
                "company": company,
                "role": role,
                "description": description.strip(),
                "adapted_from": f"{cached['company']} - {cached['role']}",
                "cached": True,
                "quality": 0.85
            },
            "response_time_ms": 1
        }
    
    def _format_same_role(self, cached_list: List[Dict], company: str, role: str) -> Dict:
        """Format Level 3: Same role"""
        
        companies = ", ".join([c['company'] for c in cached_list[:3]])
        
        # Extract core content snippet from first cached description (avoid nesting)
        sample_desc = ""
        if cached_list[0]['description']:
            desc_lines = cached_list[0]['description'].split('\n')
            # Skip header/footer lines, extract middle content
            content_lines = [line for line in desc_lines if line.strip() and 
                           not any(line.strip().startswith(m) for m in ['📋', '📊', '🔍', '🔄', 'Based on', 'Note:'])]
            if content_lines:
                sample_desc = ' '.join(content_lines[:3])[:200]  # First 3 non-header lines, max 200 chars
        
        description = f"""📋 {company} - {role}

Based on {len(cached_list)} similar {role} positions at companies like {companies}:

{sample_desc}...

Common Responsibilities:
• Software development and technical implementation
• Collaboration with cross-functional teams
• Code quality and best practices
• System design and architecture

Typical Requirements:
• Strong technical skills and problem-solving
• Team collaboration and communication
• Relevant programming languages and frameworks
• Experience with modern development practices

📊 Synthesized from: {len(cached_list)} similar role researches
🏢 Reference Companies: {companies}

Note: Role patterns are accurate, company-specific details should be verified."""
        
        return {
            "success": True,
            "provider": "local_cache",
            "match_type": "same_role",
            "company_info": {
                "company": company,
                "role": role,
                "description": description.strip(),
                "synthesized_from": len(cached_list),
                "cached": True,
                "quality": 0.75
            },
            "response_time_ms": 1
        }
    
    def _format_patterns(self, patterns: Dict, company: str, role: str) -> Dict:
        """Format Level 4: Industry patterns"""
        
        description = f"""📋 {company} - {role}

Based on {patterns['count']} similar roles in our research database:

This position typically involves professional responsibilities including development, 
collaboration, and contribution to company objectives. Companies hiring for similar 
roles generally seek candidates with relevant technical skills and experience.

Common Characteristics:
• Modern work environment and tools
• Team-based collaboration
• Professional development opportunities
• Competitive compensation packages

📊 Pattern Analysis: {patterns['count']} researches
🏢 Similar Companies: {patterns.get('companies', 'Various tech companies')[:100]}...

Note: Based on industry patterns. Verify company-specific details."""
        
        return {
            "success": True,
            "provider": "local_cache",
            "match_type": "industry_patterns",
            "company_info": {
                "company": company,
                "role": role,
                "description": description.strip(),
                "pattern_count": patterns['count'],
                "cached": True,
                "quality": 0.60
            },
            "response_time_ms": 1
        }
    
    def _format_generic(self, company: str, role: str) -> Dict:
        """Format Level 5: Enhanced generic template with real company data + role intelligence"""
        
        # Try to get real company data from Kaggle dataset
        company_data = self._get_company_info(company)
        
        # Smart role-based content
        role_lower = (role or "").lower()
        role_tips = self._get_role_specific_tips(role_lower)
        salary_estimate = self._get_salary_estimate(role_lower)
        
        # Build description with real company data if available
        if company_data:
            description = f"""📋 {company} - {role}

🏢 Company Profile:
**Industry:** {company_data['industry']}
**Company Size:** {company_data['size_range']} employees ({company_data['current_employees']:,} current)
**Location:** {company_data['locality']}, {company_data['country']}
**Founded:** {company_data['year_founded'] or 'N/A'}
**Website:** {company_data['domain'] or 'N/A'}
**LinkedIn:** {company_data['linkedin_url'] or 'N/A'}

💼 Position Overview:
{company} is seeking a {role}. Based on real company data:

{role_tips}

💰 Market Insights:
{salary_estimate}

🎯 Interview Preparation Strategy:

**Company Research:**
• Visit {company}'s website: {company_data['domain'] or 'search online'}
• Check their LinkedIn profile for recent updates
• Read Glassdoor reviews and company culture insights
• Understand their position in the {company_data['industry']} industry
• Research their competitors and market positioning

**Technical Preparation:**
• Review core concepts for {role} positions
• Prepare code examples and portfolio projects
• Practice system design scenarios
• Prepare STAR method examples for behavioral questions

**Key Questions to Ask:**
• Team structure and development practices
• Technology stack and tooling
• Growth opportunities and career path
• Current challenges the team is facing

📊 Research Quality: 75% (Real company data + enhanced template)
🔄 Live web research will be added when APIs refresh

Note: This combines verified company data from our database with intelligent role-based guidance."""
            quality = 0.75  # Higher quality with real company data
            industry = company_data['industry']
            size_range = company_data['size_range']
        else:
            # Fallback to generic template without company data
            description = f"""📋 {company} - {role}

💼 Position Overview:
{company} is seeking a {role}. While specific company details are being researched, here's what you should know:

{role_tips}

💰 Market Insights:
{salary_estimate}

🎯 Interview Preparation Strategy:

**Company Research:**
• Visit {company}'s official website and LinkedIn
• Read recent news articles and press releases
• Check Glassdoor reviews and company culture insights
• Understand their products/services and target market
• Review their tech stack on StackShare or similar platforms

**Technical Preparation:**
• Review core concepts for {role} positions
• Prepare code examples and portfolio projects
• Practice system design scenarios
• Prepare STAR method examples for behavioral questions

**Key Questions to Ask:**
• Team structure and development practices
• Technology stack and tooling
• Growth opportunities and career path
• Current challenges the team is facing

📊 Research Quality: 65% (Enhanced template with industry knowledge)
🔄 Live data will be added when research APIs refresh

Note: This is an intelligent template based on role patterns. Company-specific details will be researched soon."""
            quality = 0.65
            industry = "Technology"
            size_range = None
        
        return {
            "success": True,
            "provider": "local_cache",
            "match_type": "enhanced_template_with_data" if company_data else "enhanced_template",
            "company_info": {
                "company": company,
                "role": role,
                "description": description.strip(),
                "cached": False,
                "quality": quality,
                "salary_range": salary_estimate.split(":")[1].split("\n")[0].strip() if ":" in salary_estimate else None,
                "industry": industry,
                "company_size": size_range
            },
            "response_time_ms": 1
        }
    
    def _get_company_info(self, company: str) -> Optional[Dict]:
        """Fetch real company data from company_data table (Kaggle dataset)"""
        cursor = self.db.cursor()
        company_norm = self._normalize(company)
        
        try:
            # Try exact match first
            cursor.execute("""
            SELECT name, domain, year_founded, industry, size_range, 
                   locality, country, linkedin_url, current_employee_estimate,
                   total_employee_estimate
            FROM company_data
            WHERE name_normalized = %s
            LIMIT 1
            """, (company_norm,))
            
            row = cursor.fetchone()
            
            # If no exact match, try partial match
            if not row:
                cursor.execute("""
                SELECT name, domain, year_founded, industry, size_range,
                       locality, country, linkedin_url, current_employee_estimate,
                       total_employee_estimate
                FROM company_data
                WHERE name_normalized LIKE %s
                ORDER BY current_employee_estimate DESC
                LIMIT 1
                """, (f'%{company_norm}%',))
                row = cursor.fetchone()
            
            if row:
                return {
                    'name': row[0],
                    'domain': row[1],
                    'year_founded': row[2],
                    'industry': row[3],
                    'size_range': row[4],
                    'locality': row[5],
                    'country': row[6],
                    'linkedin_url': row[7],
                    'current_employees': row[8] or 0,
                    'total_employees': row[9] or 0
                }
        except Exception as e:
            logger.debug(f"No company data found for {company}: {e}")
        
        return None
    
    def _get_role_specific_tips(self, role_lower: str) -> str:
        """Generate role-specific insights"""
        if any(keyword in role_lower for keyword in ['engineer', 'developer', 'sde', 'software']):
            return """**Role Type:** Software Engineering
• Focus on data structures, algorithms, and system design
• Expect coding challenges (LeetCode medium-hard level)
• Be ready to discuss past projects and technical decisions
• Understand scalability, performance, and code quality principles"""
        elif any(keyword in role_lower for keyword in ['data', 'scientist', 'analyst', 'ml']):
            return """**Role Type:** Data & Analytics
• Strong foundation in statistics, SQL, and data visualization
• Expect questions on A/B testing, metrics, and experimentation
• Prepare case studies showing data-driven decision making
• Understand ML fundamentals if applicable to the role"""
        elif any(keyword in role_lower for keyword in ['product', 'manager', 'pm']):
            return """**Role Type:** Product Management
• Focus on product thinking, prioritization frameworks
• Prepare to discuss metrics, user research, and roadmapping
• Expect case studies and product design questions
• Show understanding of business impact and user needs"""
        elif any(keyword in role_lower for keyword in ['devops', 'infrastructure', 'sre']):
            return """**Role Type:** DevOps/Infrastructure
• Strong knowledge of CI/CD, containerization, and cloud platforms
• Expect questions on monitoring, reliability, and incident management
• Prepare examples of automation and infrastructure optimization
• Understand scalability and disaster recovery principles"""
        elif any(keyword in role_lower for keyword in ['frontend', 'ui', 'react', 'angular']):
            return """**Role Type:** Frontend Development
• Expert in JavaScript/TypeScript, modern frameworks (React/Vue/Angular)
• Focus on performance, accessibility, and responsive design
• Expect questions on state management and component architecture
• Prepare to discuss UI/UX principles and cross-browser compatibility"""
        elif any(keyword in role_lower for keyword in ['backend', 'api', 'microservices']):
            return """**Role Type:** Backend Development
• Strong in API design, databases, and server-side architecture
• Expect questions on scalability, caching, and distributed systems
• Prepare examples of complex backend implementations
• Understand security, authentication, and data modeling"""
        else:
            return """**Role Type:** Professional Position
• Review job description carefully for specific requirements
• Prepare examples demonstrating relevant experience
• Focus on problem-solving and collaboration abilities
• Research industry trends and company positioning"""
    
    def _get_salary_estimate(self, role_lower: str) -> str:
        """Provide salary ranges based on role type"""
        if any(keyword in role_lower for keyword in ['senior', 'lead', 'principal', 'staff']):
            return """Estimated Range: $150,000 - $250,000+ annually
Senior-level positions typically include equity and comprehensive benefits."""
        elif any(keyword in role_lower for keyword in ['junior', 'entry', 'associate']):
            return """Estimated Range: $80,000 - $130,000 annually
Entry-level positions often include training and mentorship programs."""
        elif any(keyword in role_lower for keyword in ['engineer', 'developer']):
            return """Estimated Range: $120,000 - $180,000 annually
Mid-level technical roles typically include equity compensation."""
        elif any(keyword in role_lower for keyword in ['manager', 'director']):
            return """Estimated Range: $140,000 - $220,000+ annually
Management roles often include performance bonuses and equity."""
        else:
            return """Estimated Range: $100,000 - $160,000 annually
Compensation varies based on experience, location, and company size."""
    
    def _normalize(self, text: str) -> str:
        """Normalize text for matching (lowercase, no special chars)"""
        if not text:
            return ""
        return re.sub(r'[^a-z0-9]', '', text.lower())
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        cursor = self.db.cursor()
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT company_normalized) as companies,
            COUNT(DISTINCT role_normalized) as roles,
            MAX(researched_at) as most_recent
        FROM research_cache
        """)
        
        row = cursor.fetchone()
        return {
            'total_cached': row[0] or 0,
            'unique_companies': row[1] or 0,
            'unique_roles': row[2] or 0,
            'most_recent': row[3]
        }
