import type { CandidateProfile } from './api';

export type ApplicationTruthCategory =
  | 'EXPERIENCE'
  | 'FACT'
  | 'SKILL'
  | 'EDUCATION'
  | 'CERTIFICATION'
  | 'LANGUAGE';

export type ApplicationTruthItem = {
  id: string;
  category: ApplicationTruthCategory;
  label: string;
  detail: string | null;
};

const isConfirmed = (sourceType: string) => sourceType === 'USER_CONFIRMED';

function period(
  startDate: string | null | undefined,
  endDate: string | null | undefined,
  current = false
) {
  if (!startDate) return null;
  const start = startDate.slice(0, 7);
  const end = current ? 'atual' : endDate?.slice(0, 7);
  return end ? `${start} → ${end}` : start;
}

export function buildTruthInventory(profile: CandidateProfile): ApplicationTruthItem[] {
  const items: ApplicationTruthItem[] = [];

  for (const experience of profile.experiences) {
    if (isConfirmed(experience.source_type)) {
      items.push({
        id: `experience:${experience.id}`,
        category: 'EXPERIENCE',
        label: `${experience.role_title} · ${experience.company_name}`,
        detail: period(experience.start_date, experience.end_date, experience.is_current)
      });
    }

    for (const fact of experience.facts) {
      if (!isConfirmed(fact.source_type)) continue;
      items.push({
        id: `fact:${fact.id}`,
        category: 'FACT',
        label: fact.value,
        detail: `${experience.role_title} · ${experience.company_name}`
      });
    }
  }

  for (const fact of profile.facts) {
    if (!isConfirmed(fact.source_type)) continue;
    items.push({ id: `fact:${fact.id}`, category: 'FACT', label: fact.value, detail: null });
  }

  for (const skill of profile.skills) {
    if (!isConfirmed(skill.source_type)) continue;
    const details = [
      skill.level ? `nível ${skill.level.toLocaleLowerCase('pt-BR')}` : null,
      skill.years_experience !== null && skill.years_experience !== undefined
        ? `${skill.years_experience} ano(s)`
        : null
    ].filter(Boolean);
    items.push({
      id: `skill:${skill.id}`,
      category: 'SKILL',
      label: skill.name,
      detail: details.length ? details.join(' · ') : null
    });
  }

  for (const education of profile.education) {
    if (!isConfirmed(education.source_type)) continue;
    items.push({
      id: `education:${education.id}`,
      category: 'EDUCATION',
      label: education.course,
      detail: `${education.institution} · ${education.status.toLocaleLowerCase('pt-BR')}`
    });
  }

  for (const certification of profile.certifications) {
    if (!isConfirmed(certification.source_type)) continue;
    items.push({
      id: `certification:${certification.id}`,
      category: 'CERTIFICATION',
      label: certification.name,
      detail: certification.issuer ?? null
    });
  }

  for (const language of profile.languages) {
    if (!isConfirmed(language.source_type)) continue;
    items.push({
      id: `language:${language.id}`,
      category: 'LANGUAGE',
      label: language.name,
      detail: language.proficiency.toLocaleLowerCase('pt-BR')
    });
  }

  return items;
}
