from typing import List
from sqlalchemy.orm import Session
from models import ContentFile, SearchIndex
import re

class SearchEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        normalized = self.normalize_text(text)
        words = normalized.split()
        return [w for w in words if len(w) > 2]
    
    def index_file(self, file_id: int, filename: str, description: str = "", tags: str = ""):
        self.db.query(SearchIndex).filter(SearchIndex.file_id == file_id).delete()
        
        search_text = f"{filename} {description} {tags}".lower()
        keywords = self.extract_keywords(search_text)
        
        for keyword in keywords:
            weight = self._calculate_weight(keyword, filename, description, tags)
            idx = SearchIndex(
                file_id=file_id,
                search_text=keyword,
                keyword_weight=weight
            )
            self.db.add(idx)
        
        self.db.commit()
    
    def _calculate_weight(self, keyword: str, filename: str, description: str, tags: str) -> float:
        weight = 0.0
        if keyword in filename.lower():
            weight += 3.0
        if keyword in tags.lower():
            weight += 2.5
        if keyword in description.lower():
            weight += 1.0
        return weight
    
    def search(self, query: str, limit: int = 50, offset: int = 0) -> List[ContentFile]:
        keywords = self.extract_keywords(query)
        
        if not keywords:
            return self.db.query(ContentFile).filter(
                ContentFile.is_public == True
            ).order_by(ContentFile.upload_date.desc()).limit(limit).offset(offset).all()
        
        results = self.db.query(ContentFile).join(
            SearchIndex, ContentFile.id == SearchIndex.file_id
        ).filter(
            SearchIndex.search_text.in_(keywords),
            ContentFile.is_public == True
        ).distinct(ContentFile.id).order_by(
            SearchIndex.keyword_weight.desc(),
            ContentFile.downloads.desc()
        ).limit(limit).offset(offset).all()
        
        return results
