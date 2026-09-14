from pathlib import Path

path = Path("apps/web/src/routes/+page.svelte")
text = path.read_text(encoding="utf-8")

text = text.replace("value.split(/[\n,]/)", "value.split(/[\\n,]/)")
text = text.replace(".join('\n')", ".join('\\n')")

marker = "  const provenance = () => ({ source_type: 'USER_CONFIRMED' as const, confidence: 1 });\n"
insert = """  const provenance = () => ({ source_type: 'USER_CONFIRMED' as const, confidence: 1 });
  const workModelOptions: { value: WorkModel; label: string }[] = [
    { value: 'REMOTE', label: 'Remoto' },
    { value: 'HYBRID', label: 'Híbrido' },
    { value: 'ONSITE', label: 'Presencial' }
  ];
  const contractOptions: { value: ContractType; label: string }[] = [
    { value: 'CLT', label: 'CLT' },
    { value: 'PJ', label: 'PJ' },
    { value: 'INTERNSHIP', label: 'Estágio' }
  ];
"""
if marker not in text:
    raise RuntimeError("provenance marker not found")
text = text.replace(marker, insert, 1)

old_work = """{#each [{value:'REMOTE',label:'Remoto'},{value:'HYBRID',label:'Híbrido'},{value:'ONSITE',label:'Presencial'}] as option}"""
text = text.replace(old_work, "{#each workModelOptions as option}")

old_contract = """{#each ['CLT','PJ','INTERNSHIP'] as contract}
                <label class=\"choice\"><input type=\"checkbox\" checked={form.contract_types.includes(contract)} onchange={() => form.contract_types = toggle(form.contract_types, contract)} />{contract === 'INTERNSHIP' ? 'Estágio' : contract}</label>"""
new_contract = """{#each contractOptions as option}
                <label class=\"choice\"><input type=\"checkbox\" checked={form.contract_types.includes(option.value)} onchange={() => form.contract_types = toggle(form.contract_types, option.value)} />{option.label}</label>"""
if old_contract not in text:
    raise RuntimeError("contract options marker not found")
text = text.replace(old_contract, new_contract, 1)

path.write_text(text, encoding="utf-8")
