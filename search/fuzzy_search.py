from rapidfuzz import fuzz, process

class FuzzySearchEngine:
    def init(self):
        self.common_typos = {
            'ریظی': 'ریاضی',
            'ریاضی': 'ریاضی',
            'فیزیک': 'فیزیک',
            'فیضیک': 'فیزیک',
            'شیمی': 'شیمی',
            'شیمى': 'شیمی',
            'عربی': 'عربی',
            'عربى': 'عربی',
        }
    
    def suggest_correction(self, query: str) -> str:
        subjects = ['ریاضی', 'فیزیک', 'شیمی', 'عربی', 'ادبیات', 'زیست', 'تاریخ', 'جغرافیا']
        for word in query.split():
            best_match = process.extractOne(word, subjects, scorer=fuzz.ratio)
            if best_match and best_match[1] >= 75 and best_match[0] != word:
                return query.replace(word, best_match[0])
        return None
    
    def enhance_results(self, query: str, results: list) -> list:
        scored = []
        for result in results:
            score = 0
            title = result.get('title', '') or result.get('teacher_name', '')
            if query.lower() in title.lower():
                score += 50
            fuzzy_score = fuzz.partial_ratio(query.lower(), title.lower())
            score += fuzzy_score / 2
            scored.append((result, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in scored]