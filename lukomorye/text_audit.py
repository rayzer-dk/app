"""Structural audit, not a claim of editorial collation with every source."""
import json,re,hashlib
from collections import defaultdict
from pathlib import Path
def audit_texts(out):
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    hashes=defaultdict(list);rows=[]
    for b in catalog:
        d=json.loads((out/'books'/f"{b['id']}.json").read_text(encoding='utf-8'))
        text=' '.join(x['text'] for x in d['blocks'])
        count=len(re.findall(r'\w+',text))
        digest=hashlib.sha256(re.sub(r'\W+','',text.casefold().replace('ё','е')).encode()).hexdigest()
        hashes[digest].append(b['id'])
        source=d.get('sourceUrl') or d.get('page') or b.get('page') or ''
        status='translated_from_source' if b.get('sourceType')=='translation' else 'retelling_needs_replacement' if b.get('sourceType')=='retelling' else 'edition_requires_collation'
        flags=[]
        if not source:flags.append('source_missing')
        if count<350:flags.append('short_review_not_proof_of_abridgement')
        if re.search(r'\b(сокращ[её]нный текст|продолжение следует|текст отсутствует|текст неполный|отрывок из|пока не вычитан)\b',text,re.I):flags.append('possible_fragment')
        assert d['id']==b['id'] and text.strip() and b['language']=='ru'
        rows.append({'id':b['id'],'title':b['title'],'wordCount':count,'source':source,'edition':d.get('edition',''),'status':status,'flags':flags,'sha256':hashlib.sha256((out/'books'/f"{b['id']}.json").read_bytes()).hexdigest()})
    duplicate=[v for v in hashes.values() if len(v)>1]
    assert not duplicate
    result={'total':len(rows),'structuralAudit':'all texts inspected for presence, declared language, exact normalized duplicates, source, short length and fragment markers; not independent line-by-line collation','fullTranslations':sum(r['status']=='translated_from_source' for r in rows),'retellingsPending':sum(r['status']=='retelling_needs_replacement' for r in rows),'exactDuplicates':duplicate,'shortTexts':sum('short_review_not_proof_of_abridgement' in r['flags'] for r in rows),'books':rows}
    (out/'TEXT_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
