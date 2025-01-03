"""AI-powered HR analysis module."""

import anthropic
from typing import Dict, Any
import logging
import re

class AIHRAnalyzer:
    def __init__(self, api_key: str):
        """Initialize AI HR analyzer."""
        self.client = anthropic.Client(api_key=api_key)
    
    def generate_hr_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HR analysis from WPR data."""
        try:
            # Prepare submission text
            submission_text = self._prepare_submission_text(data)
            
            # Get system prompt
            system_prompt = self._get_system_prompt(data['Week Number'])
            
            # Get AI analysis
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Please analyze this Weekly Productivity Report and provide comprehensive feedback following the specified format: \n\n{submission_text}"
                }]
            )
            
            if not response or not response.content:
                raise ValueError("Empty response from AI")
            
            ai_response = response.content[0].text
            
            # Extract metrics from AI response
            metrics = self._extract_metrics(ai_response)
            
            # Extract recommendations
            recommendations = self._extract_recommendations(ai_response)
            
            return {
                "report_id": data.get('report_id'),
                "team_member_id": data.get('team_member_id'),
                "week_number": data['Week Number'],
                "year": data['Year'],
                "analysis_text": ai_response,
                "metrics": metrics,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logging.error(f"Error generating HR analysis: {str(e)}")
            return {
                "report_id": data.get('report_id'),
                "team_member_id": data.get('team_member_id'),
                "week_number": data['Week Number'],
                "year": data['Year'],
                "analysis_text": f"Error generating analysis: {str(e)}",
                "metrics": {},
                "recommendations": []
            }
    
    def _prepare_submission_text(self, data: Dict[str, Any]) -> str:
        """Prepare submission text for AI analysis."""
        return f"""
        Name: {data['Name']}
        Team: {data['Team']}
        Week Number: {data['Week Number']}
        Year: {data['Year']}
        
        Completed Tasks: {data['Completed Tasks']}
        Pending Tasks: {data['Pending Tasks']}
        Dropped Tasks: {data.get('Dropped Tasks', [])}
        
        Projects: {data.get('Projects', [])}
        
        Productivity Rating: {data['Productivity Rating']}
        Productivity Suggestions: {data.get('Productivity Suggestions', [])}
        Productivity Details: {data.get('Productivity Details', '')}
        
        Most Productive Time: {data.get('Productive Time', '')}
        Preferred Work Location: {data.get('Productive Place', '')}
        
        Peer Evaluations: {data.get('Peer_Evaluations', {})}
        """
    
    def _get_system_prompt(self, week_number: int) -> str:
        """Get system prompt for AI analysis."""
        return f"""You are an empathetic HR productivity expert and career coach for IOL Inc.
        Your role is to analyze Weekly Productivity Reports (WPR) and provide personalized, actionable feedback.
        
        Your analysis should include:
        1. Achievement highlights
        2. Performance metrics
        3. Growth opportunities
        4. Action plan for next week
        5. Team collaboration insights
        6. Productivity optimization suggestions
        7. Wellness check
        8. Priority management
        
        Format your response in HTML with appropriate styling.
        Be specific, actionable, and maintain a supportive tone.
        Focus on both immediate improvements and long-term growth.
        """
    
    def _extract_metrics(self, analysis_text: str) -> Dict[str, Any]:
        """Extract performance metrics from AI analysis."""
        try:
            # Initialize default metrics
            metrics = {
                'productivity_score': 0,
                'task_completion_rate': 0,
                'project_progress': 0,
                'collaboration_score': 0
            }
            
            # Extract metrics from AI analysis text
            # Look for numeric values following metric keywords
            import re
            
            # Extract productivity score (assumed to be on a 0-4 scale)
            if prod_match := re.search(r'productivity[^0-9]*([0-4](?:\.\d)?)', analysis_text, re.I):
                metrics['productivity_score'] = float(prod_match.group(1))
            
            # Extract task completion rate percentage
            if task_match := re.search(r'task completion[^0-9]*(\d{1,3})%', analysis_text, re.I):
                metrics['task_completion_rate'] = int(task_match.group(1))
            
            # Extract project progress percentage
            if proj_match := re.search(r'project progress[^0-9]*(\d{1,3})%', analysis_text, re.I):
                metrics['project_progress'] = int(proj_match.group(1))
            
            # Extract collaboration score (assumed to be on a 0-4 scale)
            if collab_match := re.search(r'collaboration[^0-9]*([0-4](?:\.\d)?)', analysis_text, re.I):
                metrics['collaboration_score'] = float(collab_match.group(1))
            
            return metrics
        except Exception as e:
            logging.error(f"Error extracting metrics: {str(e)}")
            return {
                'productivity_score': 0,
                'task_completion_rate': 0,
                'project_progress': 0,
                'collaboration_score': 0
            }

    def _extract_recommendations(self, analysis_text: str) -> Dict[str, Any]:
        """Extract structured recommendations and insights from AI analysis."""
        try:
            recommendations = {
                'immediate_actions': [],
                'growth_recommendations': {},
                'wellness_indicators': {
                    'work_life_balance': 'N/A',
                    'workload_assessment': 'N/A',
                    'engagement_level': 'N/A'
                }
            }
            
            # Split analysis into sections
            sections = analysis_text.split('\n')
            
            current_section = ''
            for line in sections:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Detect section headers
                if line.lower().startswith('action plan') or line.lower().startswith('recommendations'):
                    current_section = 'actions'
                    continue
                elif line.lower().startswith('wellness') or line.lower().startswith('well-being'):
                    current_section = 'wellness'
                    continue
                
                # Process lines based on current section
                if current_section == 'actions' and line.startswith('•'):
                    recommendations['immediate_actions'].append(line[1:].strip())
                elif current_section == 'wellness':
                    # Extract wellness indicators
                    if 'work-life balance' in line.lower():
                        recommendations['wellness_indicators']['work_life_balance'] = self._extract_wellness_value(line)
                    elif 'workload' in line.lower():
                        recommendations['wellness_indicators']['workload_assessment'] = self._extract_wellness_value(line)
                    elif 'engagement' in line.lower():
                        recommendations['wellness_indicators']['engagement_level'] = self._extract_wellness_value(line)
            
            # Ensure we have at least some recommendations
            if not recommendations['immediate_actions']:
                recommendations['immediate_actions'] = ['Focus on task prioritization',
                                                     'Maintain regular communication with team',
                                                     'Document progress consistently']
            
            return recommendations
        except Exception as e:
            logging.error(f"Error extracting recommendations: {str(e)}")
            return {
                'immediate_actions': [],
                'growth_recommendations': {},
                'wellness_indicators': {
                    'work_life_balance': 'N/A',
                    'workload_assessment': 'N/A',
                    'engagement_level': 'N/A'
                }
            }
    
    def _extract_wellness_value(self, line: str) -> str:
        """Helper method to extract wellness indicator values."""
        try:
            # Remove bullet points and split by common separators
            parts = line.replace('•', '').replace(':', '').replace('-', '').strip().split()
            # Return the last part as the value
            return parts[-1] if parts else 'N/A'
        except Exception:
            return 'N/A'
