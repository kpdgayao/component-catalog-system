"""Input validation module for WPR application."""

import re
from typing import List, Dict, Any
import logging

class InputValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        try:
            if not email:
                return False
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            return bool(re.match(pattern, email))
        except Exception as e:
            logging.error(f"Error validating email: {str(e)}")
            return False

    @staticmethod
    def validate_tasks(tasks: str) -> List[str]:
        """Validate and clean task input."""
        try:
            if not tasks:
                return []
            
            # Split tasks by newline and remove empty lines
            task_list = [task.strip() for task in tasks.split('\n') if task.strip()]
            
            # Remove any potentially harmful characters
            cleaned_tasks = [re.sub(r'[^\w\s\-.,()\'\"]+', '', task) for task in task_list]
            return cleaned_tasks
        except Exception as e:
            logging.error(f"Error validating tasks: {str(e)}")
            return []

    @staticmethod
    def validate_projects(projects_str: str) -> List[Dict[str, Any]]:
        """Validate and parse project entries."""
        if not projects_str:
            return []
            
        validated_projects = []
        for line in projects_str.strip().split('\n'):
            try:
                project_name, completion = line.rsplit(',', 1)
                project_name = project_name.strip()
                completion = int(completion.strip().rstrip('%'))
                
                if not project_name:
                    logging.warning(f"Empty project name in line: {line}")
                    continue
                    
                if not (0 <= completion <= 100):
                    logging.warning(f"Invalid completion percentage ({completion}%) for project: {project_name}")
                    continue
                    
                validated_projects.append({
                    "name": project_name,
                    "completion": completion
                })
                
            except ValueError:
                logging.warning(f"Invalid project format: {line}")
                continue
                
        return validated_projects

    @staticmethod
    def validate_peer_ratings(ratings: Dict[str, Any]) -> Dict[str, int]:
        """Validate peer ratings.
        
        Expected format:
        {
            'peer_name': '1 (Poor)' | '2 (Fair)' | '3 (Good)' | '4 (Excellent)'
        }
        """
        try:
            validated_ratings = {}
            for peer, rating in ratings.items():
                try:
                    if isinstance(rating, (int, float)):
                        numeric_rating = int(rating)
                    else:
                        # Extract numeric value from rating string (e.g., "1 (Poor)" -> 1)
                        numeric_rating = int(str(rating).split()[0])
                    
                    if 1 <= numeric_rating <= 4:
                        validated_ratings[peer] = numeric_rating
                    else:
                        logging.warning(f"Rating out of range (1-4) for {peer}: {rating}")
                except (ValueError, IndexError):
                    logging.warning(f"Invalid rating format for {peer}: {rating}")
                    continue
            return validated_ratings
        except Exception as e:
            logging.error(f"Error validating peer ratings: {str(e)}")
            return {}

    @staticmethod
    def validate_productivity_rating(rating: Any) -> int:
        """Validate productivity rating (1-4 scale)."""
        try:
            if isinstance(rating, str):
                # Extract numeric value if string (e.g., "3 - Good" -> 3)
                rating = int(rating.split()[0])
            else:
                rating = int(rating)
            
            return rating if 1 <= rating <= 4 else 0
        except (ValueError, IndexError, TypeError):
            logging.warning(f"Invalid productivity rating format: {rating}")
            return 0

    @staticmethod
    def validate_suggestions(suggestions: List[str]) -> List[str]:
        """Validate productivity improvement suggestions."""
        try:
            if not suggestions:
                return []
            
            # Remove empty strings and clean each suggestion
            cleaned = []
            for suggestion in suggestions:
                if isinstance(suggestion, str) and suggestion.strip():
                    # Remove potentially harmful characters
                    cleaned_suggestion = re.sub(r'[^\w\s\-.,()\'\"]+', '', suggestion.strip())
                    if cleaned_suggestion:
                        cleaned.append(cleaned_suggestion)
            
            return cleaned
        except Exception as e:
            logging.error(f"Error validating suggestions: {str(e)}")
            return []
