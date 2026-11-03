(() => {
  const configs = {
    education_records: {
      title: 'Освіта', fields: [
        ['level', 'Рівень освіти', 'select', ['', 'Оберіть рівень', 'Середня освіта', 'Середня спеціальна освіта', 'Професійно-технічна освіта', 'Незакінчена вища освіта', 'Бакалаврат', 'Магістратура', 'Докторантура', 'Інше']],
        ['school', 'Навчальний заклад', 'text'], ['major', 'Спеціальність', 'text'], ['years', 'Роки навчання', 'text'],
        ['status', 'Статус навчання', 'select', ['', 'Оберіть статус', 'Навчаюся', 'Завершено', 'Не завершено']]
      ]
    },
    experience_records: { title: 'Місце роботи', fields: [['position', 'Посада', 'text'], ['company', 'Компанія', 'text'], ['years', 'Період роботи', 'text'], ['description', 'Обов’язки та досягнення', 'textarea']] },
    language_records: { title: 'Мова', fields: [['language', 'Мова', 'text'], ['level', 'Рівень', 'select', ['', 'Оберіть рівень', 'Початковий (A1)', 'Нижче середнього (A2)', 'Середній (B1)', 'Вище середнього (B2)', 'Просунутий (C1)', 'Вільне володіння (C2)', 'Рідна мова']]] },
    skill_records: { title: 'Навичка', fields: [['category', 'Категорія', 'select', ['', 'Оберіть категорію', 'Програмування', 'Дизайн', 'Маркетинг', 'Управління', 'Аналітика', 'Комунікація', 'Інструменти та програми', 'Інше']], ['skill', 'Навичка', 'text'], ['level', 'Рівень володіння', 'select', ['', 'Не вказувати', 'Базовий', 'Середній', 'Просунутий', 'Експертний']]] }
  };

  const parse = (input) => {
    try { const value = JSON.parse(input.value || '[]'); return Array.isArray(value) ? value : []; }
    catch { return String(input.value || '').split(/\r?\n/).filter(Boolean).map(line => {
      const values = line.split('|').map(part => part.trim());
      return Object.fromEntries(values.map((value, index) => [index === 0 ? 'level' : `legacy${index}`, value]));
    }); }
  };

  document.querySelectorAll('[data-record-group]').forEach(group => {
    const key = group.dataset.recordGroup;
    const config = configs[key];
    const hidden = group.querySelector(`input[name="${key}"]`);
    const list = group.querySelector('[data-record-list]');
    if (!config || !hidden || !list) return;

    const createRow = (values = {}, isDraft = false) => {
      const row = document.createElement('fieldset');
      row.className = 'record-card';
      if (isDraft) row.dataset.draft = 'true';
      const legend = document.createElement('legend'); legend.textContent = config.title; row.append(legend);
      config.fields.forEach(([name, label, type, options]) => {
        const wrap = document.createElement('label'); wrap.className = 'form-field record-field'; wrap.textContent = label;
        let control;
        if (type === 'select') {
          control = document.createElement('select');
          options.forEach((option, index) => {
            const item = document.createElement('option');
            item.value = index < 2 ? (index === 0 ? '' : '') : option;
            item.textContent = option;
            control.append(item);
          });
          if (values[name] && ![...control.options].some(option => option.value === values[name])) {
            const custom = document.createElement('option'); custom.value = values[name]; custom.textContent = values[name]; control.append(custom);
          }
          control.value = values[name] || '';
        } else {
          control = document.createElement(type === 'textarea' ? 'textarea' : 'input');
          if (type !== 'textarea') control.type = 'text';
          control.value = values[name] || '';
          if (type === 'textarea') control.rows = 3;
        }
        control.name = `${key}__${name}`; control.dataset.recordField = name;
        wrap.append(control); row.append(wrap);
      });
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'link-button record-remove'; remove.textContent = 'Видалити запис';
      remove.addEventListener('click', () => { row.remove(); sync(); if (isDraft) setDraftOpen(false); }); row.append(remove);
      const updateDraftState = () => {
        const hasContent = [...row.querySelectorAll('[data-record-field]')].some(input => input.value.trim());
        if (hasContent) { delete row.dataset.draft; setDraftOpen(false); }
        else if (isDraft) { row.dataset.draft = 'true'; setDraftOpen(!row.hidden); }
        sync();
      };
      row.addEventListener('input', updateDraftState); row.addEventListener('change', updateDraftState); list.append(row);
    };
    const sync = () => {
      const rows = [...list.querySelectorAll('.record-card')].map(row => Object.fromEntries([...row.querySelectorAll('[data-record-field]')].map(input => [input.dataset.recordField, input.value.trim()]))).filter(row => Object.values(row).some(Boolean));
      hidden.value = JSON.stringify(rows);
    };
    const existing = parse(hidden);
    existing.forEach(createRow);
    const addButton = group.querySelector('[data-add-record]');
    addButton?.setAttribute('aria-expanded', 'false');
    const buttonText = addButton?.firstChild;
    const addLabel = buttonText?.textContent?.trim() || 'Додати запис';
    const setDraftOpen = (open) => {
      addButton?.setAttribute('aria-expanded', String(open));
      if (buttonText) buttonText.textContent = open ? 'Сховати форму ' : `${addLabel} `;
    };
    addButton?.addEventListener('click', () => {
      const emptyDraft = [...list.querySelectorAll('[data-draft="true"]')].find(row =>
        ![...row.querySelectorAll('[data-record-field]')].some(input => input.value.trim())
      );
      if (emptyDraft) {
        emptyDraft.hidden = !emptyDraft.hidden;
        setDraftOpen(!emptyDraft.hidden);
        if (!emptyDraft.hidden) emptyDraft.querySelector('input,select,textarea')?.focus();
        return;
      }
      createRow({}, true);
      sync();
      setDraftOpen(true);
      list.lastElementChild?.querySelector('input,select,textarea')?.focus();
    });
    if (!existing.length) hidden.value = '[]'; else sync();
  });

  const form = document.querySelector('.resume-editor-form');
  form?.addEventListener('submit', () => {
    // Keep the existing document fields populated for older templates and saved resumes.
    const collect = key => [...document.querySelectorAll(`[data-record-group="${key}"] .record-card`)].map(row => [...row.querySelectorAll('[data-record-field]')].map(input => input.value.trim()).filter(Boolean).join(' · ')).filter(Boolean).join('\n');
    const education = collect('education_records');
    const experience = collect('experience_records');
    const skills = collect('skill_records');
    const fields = { education, experience, skills };
    Object.entries(fields).forEach(([name, value]) => {
      const hidden = form.querySelector(`input[name="${name}"]`);
      if (hidden) hidden.value = value;
    });
    const firstLevel = document.querySelector('[data-record-group="education_records"] [data-record-field="level"]')?.value || '';
    const oldLevel = form.querySelector('input[name="education_level"]'); if (oldLevel) oldLevel.value = firstLevel;
  });
})();
