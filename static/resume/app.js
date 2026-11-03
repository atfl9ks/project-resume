const authDialog = document.querySelector('#authDialog');
const templateDialog = document.querySelector('#templateDialog');
let toast = document.querySelector('.toast');
let toastTimer;

// Mobile/older-browser fallback for scroll-driven story motion. Uses one
// passive scroll listener + rAF and only transforms/opacity (no layout reads
// after writes). Native CSS timelines remain preferred where supported.
if (document.querySelector('.hero-art')) {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const smallScreen = window.matchMedia('(max-width: 680px)');
  const hasScrollTimelines = CSS.supports('animation-timeline: view()') && CSS.supports('animation-range: entry 0% exit 100%');
  if (!reduceMotion.matches && (smallScreen.matches || !hasScrollTimelines)) {
    document.documentElement.classList.add('scroll-js-fallback');
    const storyItems = [...document.querySelectorAll('.hero-copy,.hero-art,.floating-note,.template-card,.section-heading>div,.step,.quote-inner,.trust-strip')];
    let storyFrame = 0;
    const clamp01 = value => Math.max(0, Math.min(1, value));
    const updateStory = () => {
      storyFrame = 0;
      const vh = window.innerHeight || 700;
      for (const item of storyItems) {
        const rect = item.getBoundingClientRect();
        const progress = clamp01((vh * .9 - rect.top) / (vh * .72 + rect.height));
        const offset = (1 - progress) * (smallScreen.matches ? 20 : 30);
        const scale = 0.965 + progress * 0.035;
        item.style.opacity = String(.28 + progress * .72);
        item.style.transform = `translate3d(0, ${offset.toFixed(1)}px, 0) scale(${scale.toFixed(3)})`;
      }
      const art = document.querySelector('.hero-art');
      if (art) {
        const progress = clamp01(window.scrollY / (smallScreen.matches ? 430 : 520));
        art.style.setProperty('--story-scale', String(.94 + progress * .08));
      }
    };
    const requestStoryUpdate = () => {
      if (!storyFrame) storyFrame = window.requestAnimationFrame(updateStory);
    };
    window.addEventListener('scroll', requestStoryUpdate, { passive: true });
    window.addEventListener('resize', requestStoryUpdate, { passive: true });
    reduceMotion.addEventListener?.('change', event => {
      if (event.matches) {
        window.removeEventListener('scroll', requestStoryUpdate);
        window.removeEventListener('resize', requestStoryUpdate);
        document.documentElement.classList.remove('scroll-js-fallback');
        storyItems.forEach(item => { item.style.opacity = ''; item.style.transform = ''; });
      } else requestStoryUpdate();
    });
    requestStoryUpdate();
  }
}

// The anchor hash is the navigation source of truth; scroll observation keeps
// the selected tab in sync when the user moves through the landing page.
const mainNav = document.querySelector('.main-nav');
if (mainNav) {
  const navLinks = [...mainNav.querySelectorAll('a[href^="#"]')];
  const navSections = navLinks.map(link => document.querySelector(link.getAttribute('href'))).filter(Boolean);
  const indicator = document.createElement('span');
  indicator.className = 'nav-indicator';
  indicator.setAttribute('aria-hidden', 'true');
  mainNav.append(indicator);
  let clickNavigationLock = false;
  let navigationUnlockTimer;
  const activateLink = (link, updateHash = false) => {
    if (!link) return;
    navLinks.forEach(item => {
      const active = item === link;
      item.classList.toggle('active', active);
      if (active) item.setAttribute('aria-current', 'location');
      else item.removeAttribute('aria-current');
    });
    const navBox = mainNav.getBoundingClientRect();
    const linkBox = link.getBoundingClientRect();
    const dotSize = 7;
    indicator.style.width = `${dotSize}px`;
    indicator.style.transform = `translateX(${linkBox.left - navBox.left + (linkBox.width - dotSize) / 2}px)`;
    if (updateHash && location.hash !== link.hash) history.replaceState(null, '', link.hash);
  };
  const syncFromUrl = () => activateLink(navLinks.find(link => link.hash === location.hash) || navLinks[0]);
  const finishClickNavigation = () => {
    clickNavigationLock = false;
    clearTimeout(navigationUnlockTimer);
  };
  window.addEventListener('scrollend', finishClickNavigation, { passive: true });
  navLinks.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    activateLink(link);
    clickNavigationLock = true;
    clearTimeout(navigationUnlockTimer);
    if (location.hash !== link.hash) history.pushState(null, '', link.hash);
    const section = document.querySelector(link.hash);
    section?.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      block: 'start'
    });
    navigationUnlockTimer = window.setTimeout(finishClickNavigation, 1400);
  }));
  window.addEventListener('hashchange', syncFromUrl);
  window.addEventListener('popstate', syncFromUrl);
  window.addEventListener('resize', syncFromUrl);
  syncFromUrl();
  let scrollFrame = 0;
  const syncFromScroll = () => {
    scrollFrame = 0;
    if (clickNavigationLock || !navSections.length) return;
    const probe = window.innerHeight * 0.34;
    let activeIndex = 0;
    navSections.forEach((section, index) => {
      if (section.getBoundingClientRect().top <= probe) activeIndex = index;
    });
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) activeIndex = navSections.length - 1;
    const activeLink = navLinks[activeIndex];
    if (activeLink && !activeLink.classList.contains('active')) activateLink(activeLink, true);
  };
  window.addEventListener('scroll', () => {
    if (!scrollFrame) scrollFrame = window.requestAnimationFrame(syncFromScroll);
  }, { passive: true });
  window.addEventListener('resize', syncFromScroll, { passive: true });
}

function showToast(message) {
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'status');
    document.body.append(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

function setAuthMode(mode) {
  const signup = mode === 'signup';
  const form = document.querySelector('#authForm');
  if (!form) return;
  const passwordInput = form.querySelector('[data-password-input]');
  const confirmationInput = form.querySelector('[data-password-confirm]');
  if (form.dataset.passwordSignup !== String(signup)) {
    if (passwordInput) passwordInput.value = '';
    if (confirmationInput) confirmationInput.value = '';
    const feedback = form.querySelector('[data-password-match]');
    if (feedback) feedback.textContent = '';
  }

  document.querySelector('#dialogTitle').textContent = signup
    ? 'Почнімо з резюме'
    : 'Раді бачити знову';
  document.querySelector('#dialogCopy').textContent = signup
    ? 'Створи акаунт, щоб зберігати й редагувати свої резюме.'
    : 'Увійди, щоб продовжити роботу зі своїми резюме.';
  document.querySelector('#authSubmit').innerHTML = signup
    ? 'Створити акаунт <span>↗</span>'
    : 'Увійти <span>↗</span>';
  document.querySelector('#authSwitch').innerHTML = signup
    ? 'Вже маєш акаунт? <button type="button" data-open-auth="login">Увійти</button>'
    : 'Ще не маєш акаунта? <button type="button" data-open-auth="signup">Зареєструватися</button>';

  form.action = signup ? '/register/' : '/login/';
  document.querySelector('#signupFields').hidden = !signup;
  const passwordTools = document.querySelector('#signupPasswordTools');
  passwordTools.hidden = false;
  passwordTools.querySelector('[data-password-meter]').hidden = !signup;
  passwordTools.querySelector('[data-password-confirm]').closest('label').hidden = !signup;
  form.dataset.passwordSignup = signup ? 'true' : 'false';
  form.elements.username.required = signup;
  form.elements.display_name.required = signup;
  form.elements.password2.required = signup;
  passwordInput.name = signup ? 'password1' : 'password';
  document.querySelector('#authSubmit').disabled = false;
  refreshPasswordMeters();
}

const passwordLevels = ['Дуже слабкий', 'Слабкий', 'Середній', 'Надійний', 'Дуже надійний'];
const predictablePasswordPattern = /password|passw0rd|qwerty|letmein|welcome|admin|пароль|йцукен|123456|654321|iloveyou|sunshine|football/i;
const sequentialPasswordPattern = /(?:0123|1234|2345|3456|4567|5678|6789|9876|8765|7654|6543|5432|4321|abcd|bcde|cdef|defg|qwer|wert|erty|asdf|sdfg|zxcv)/i;

function evaluatePassword(password) {
  const rules = {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    digit: /[0-9]/.test(password),
    special: /[^A-Za-z0-9\s]/.test(password),
  };
  if (!password) return { rules, score: -1, predictable: false, sequential: false };
  const pool = (/[a-z]/.test(password) ? 26 : 0) + (/[A-Z]/.test(password) ? 26 : 0) + (/[0-9]/.test(password) ? 10 : 0) + (/[^A-Za-z0-9\s]/.test(password) ? 32 : 0);
  let entropy = password.length * Math.log2(Math.max(pool, 1));
  const predictable = predictablePasswordPattern.test(password);
  const sequential = sequentialPasswordPattern.test(password) || /(.)\1{2,}/.test(password);
  if (predictable) entropy -= 38;
  if (sequential) entropy -= 22;
  if (password.length < 8) entropy = 0;
  let score = entropy < 28 ? 0 : entropy < 38 ? 1 : entropy < 52 ? 2 : entropy < 72 ? 3 : 4;
  const satisfied = Object.values(rules).filter(Boolean).length;
  if (predictable) score = 0;
  else if (sequential) score = Math.min(score, 1);
  if (satisfied < 3) score = Math.min(score, 1);
  else if (satisfied === 3) score = Math.min(score, 2);
  else if (satisfied === 4) score = Math.min(score, 3);
  return { rules, score, predictable, sequential };
}

function refreshPasswordMeters() {
  document.querySelectorAll('[data-password-meter]').forEach(meter => {
    const form = meter.closest('form');
    const password = form?.querySelector('[data-password-input]');
    if (!password) return;
    const value = password.value;
    const evaluation = evaluatePassword(value);
    const { rules, score, predictable, sequential } = evaluation;
    const strengthLabel = meter.querySelector('[data-strength-label]');
    const strengthValue = meter.querySelector('[data-strength-value]');
    const strengthHint = meter.querySelector('[data-strength-hint]');
    const track = meter.querySelector('[data-strength-track]');
    meter.dataset.strength = value ? String(score) : 'empty';
    strengthLabel.textContent = value ? passwordLevels[score] : 'Додайте пароль';
    strengthValue.textContent = value ? `${score + 1} / 5` : '0 / 5';
    track.setAttribute('aria-valuenow', String(value ? score + 1 : 0));
    track.setAttribute('aria-valuetext', value ? passwordLevels[score] : 'Пароль не введено');
    meter.querySelectorAll('[data-meter-segment]').forEach((segment, index) => {
      segment.classList.toggle('is-filled', Boolean(value) && index <= score);
    });
    meter.querySelectorAll('[data-password-rule]').forEach(item => {
      const passed = rules[item.dataset.passwordRule];
      item.classList.toggle('is-passed', passed);
      item.querySelector('.requirement-icon').textContent = passed ? '✓' : '○';
    });
    const missing = Object.entries(rules).find(([, passed]) => !passed)?.[0];
    const hints = {
      length: 'Додайте більше символів — потрібно щонайменше 8.',
      upper: 'Додайте велику літеру A–Z.',
      lower: 'Додайте малу літеру a–z.',
      digit: 'Додайте хоча б одну цифру.',
      special: 'Додайте спеціальний символ, наприклад ! або #.',
    };
    if (missing) strengthHint.textContent = hints[missing];
    else if (predictable) strengthHint.textContent = 'Уникайте поширених паролів і комбінацій на кшталт Password123.';
    else if (sequential) strengthHint.textContent = 'Уникайте простих послідовностей і повторів символів.';
    else if (score < 2) strengthHint.textContent = 'Зробіть пароль довшим і менш передбачуваним.';
    else if (score < 4) strengthHint.textContent = 'Пароль достатньо надійний; додайте ще кілька різних символів.';
    else strengthHint.textContent = 'Ваш пароль достатньо надійний.';
    const confirmation = form.querySelector('[data-password-confirm]');
    const feedback = form.querySelector('[data-password-match]');
    let matches = true;
    if (confirmation && feedback) {
      matches = Boolean(confirmation.value) && confirmation.value === value;
      feedback.textContent = !confirmation.value ? '' : matches ? 'Паролі збігаються.' : 'Паролі не збігаються.';
      feedback.classList.toggle('is-match', Boolean(confirmation.value) && matches);
      feedback.classList.toggle('is-mismatch', Boolean(confirmation.value) && !matches);
    }
    const requirementsPassed = Object.values(rules).every(Boolean);
    const canSubmit = requirementsPassed && score >= 2 && matches;
    const submit = form.querySelector('[data-registration-submit]');
    if (submit && form.dataset.passwordSignup !== 'false') submit.disabled = !canSubmit;
  });
}

document.querySelectorAll('[data-password-input], [data-password-confirm]').forEach(input => {
  input.addEventListener('input', refreshPasswordMeters);
  input.addEventListener('change', refreshPasswordMeters);
});
document.querySelectorAll('[data-registration-submit]').forEach(button => {
  const form = button.closest('form');
  form?.addEventListener('submit', event => {
    refreshPasswordMeters();
    if (button.disabled) {
      event.preventDefault();
      form.querySelector('[data-password-input]')?.focus();
    }
  });
});
refreshPasswordMeters();

document.addEventListener('click', event => {
  const visibilityButton = event.target.closest('[data-toggle-password]');
  if (!visibilityButton) return;
  const input = visibilityButton.closest('.password-input-wrap')?.querySelector('input');
  if (!input) return;
  const show = input.type === 'password';
  input.type = show ? 'text' : 'password';
  visibilityButton.classList.toggle('is-visible', show);
  visibilityButton.setAttribute('aria-pressed', String(show));
  visibilityButton.setAttribute('aria-label', show ? 'Приховати пароль' : 'Показати пароль');
  input.focus();
});

document.addEventListener('click', (event) => {
  const authButton = event.target.closest('[data-open-auth]');
  if (authButton) {
    setAuthMode(authButton.dataset.openAuth);
    if (authDialog && !authDialog.open) authDialog.showModal();
    return;
  }

  const templateButton = event.target.closest('[data-template]');
  if (templateButton) {
    const previews = {
      classic: { description: 'Для консервативних роботодавців: послідовна історія кар’єри, освіта та досвід в одній колонці.', markup: '<article class="sample-cv sample-classic"><header><strong>Олена Коваленко</strong><small>Product Designer · Київ · olena@email.com</small></header><section><b>ПРОФІЛЬ</b><p>Досвід створення цифрових продуктів і розвитку команд.</p></section><section><b>ДОСВІД РОБОТИ</b><p>Senior Designer · Bright Studio · 2022—дотепер</p></section><section><b>ОСВІТА</b><p>Графічний дизайн · КНУТД</p></section><section><b>НАВИЧКИ</b><p>Дослідження · Прототипування · Figma</p></section></article>' },
      modern: { description: 'Для IT і бізнесу: контакти, навички та освіта зібрані збоку, досвід і проєкти — у головній колонці.', markup: '<article class="sample-cv sample-modern"><aside><strong>Олена<br>Коваленко</strong><small>Product Designer</small><b>КОНТАКТИ</b><small>Київ<br>olena@email.com</small><b>НАВИЧКИ</b><small>Figma · UX<br>Аналітика</small><b>ОСВІТА</b><small>КНУТД · 2020</small></aside><div><section><b>ПРОФІЛЬ</b><p>Створюю зрозумілі цифрові продукти.</p></section><section><b>ДОСВІД</b><p>Senior Designer<br>Bright Studio · 2022—дотепер</p></section><section><b>ПРОЄКТИ</b><p>Мобільний банкінг · зростання конверсії +24%</p></section></div></article>' },
      minimal: { description: 'Для лаконічної самопрезентації: мінімум декору, більше простору для змісту й результатів.', markup: '<article class="sample-cv sample-minimal"><header><small>ПРОФЕСІЙНИЙ ПРОФІЛЬ</small><strong>Олена Коваленко</strong><small>Product Designer　/　Київ　/　olena@email.com</small></header><section><b>ПРОФІЛЬ</b><p>Проєктую цифрові продукти з фокусом на користувачах і вимірюваному результаті.</p></section><section><b>ДОСВІД</b><p>Bright Studio　·　Senior Designer　·　2022—дотепер</p></section><section><b>РЕЗУЛЬТАТИ</b><p>Збільшила конверсію онбордингу на 24%.</p></section><section><b>ОСВІТА · НАВИЧКИ</b><p>КНУТД　·　Figma　·　Дослідження</p></section></article>' },
      creative: { description: 'Для творчих фахівців: яскрава авторська шапка й акцент на проєктах та портфоліо.', markup: '<article class="sample-cv sample-creative"><header><small>КРЕАТИВНЕ ПОРТФОЛІО　✳</small><strong>Олена<br>Коваленко</strong><small>ДИЗАЙНЕРКА ЦИФРОВИХ ПРОДУКТІВ</small><p>Ідеї, що перетворюються на досвід.</p></header><div class="sample-creative-grid"><section><b>ВИБРАНІ ПРОЄКТИ</b><p>01　Мобільний банкінг<br>02　Нова айдентика<br>03　Дизайн-система</p><b>ПРОФІЛЬ</b><p>Дизайн, стратегія та робота з командами.</p></section><aside><b>ІНСТРУМЕНТИ</b><p>Figma · ProtoPie</p><b>ОСВІТА</b><p>КНУТД · Дизайн</p><b>КОНТАКТ</b><p>olena@email.com</p></aside></div></article>' }
    };
    const preview = previews[templateButton.dataset.templateId];
    document.querySelector('#templateTitle').textContent =
      templateButton.dataset.template;
    document.querySelector('#templateDescription').textContent = preview?.description || '';
    document.querySelector('#templatePreview').innerHTML = preview?.markup || '';
    templateDialog.dataset.templateId = templateButton.dataset.templateId;
    templateDialog.showModal();
    return;
  }

  if (event.target.matches('.dialog-close')) {
    event.target.closest('dialog').close();
    return;
  }

  if (event.target.matches('.choose-template')) {
    const templateId = templateDialog.dataset.templateId;
    if (!templateId) {
      showToast('Спочатку оберіть шаблон');
      return;
    }

    templateDialog.close();
    if (document.body.dataset.authenticated === 'true') {
      window.location.href = `/resumes/new/?template=${encodeURIComponent(templateId)}`;
    } else {
      setAuthMode('signup');
      authDialog.showModal();
    }
    return;
  }

  const menuButton = event.target.closest('.menu-toggle');
  if (menuButton) {
    const nav = document.querySelector('.main-nav');
    nav.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', nav.classList.contains('open'));
  }
});

document.querySelector('.main-nav')?.addEventListener('click', (event) => {
  if (event.target.closest('a')) {
    document.querySelector('.main-nav').classList.remove('open');
  }
});

document.querySelectorAll('a[href="#templates"]').forEach((link) => {
  link.addEventListener('click', () => {
    if (link.classList.contains('btn')) {
      showToast('Обери шаблон, щоб переглянути його');
    }
  });
});

[authDialog, templateDialog].filter(Boolean).forEach((dialog) => {
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
});

// Avatar editor: crop and resize locally, then persist the resulting image on the server.
const avatarDialog = document.querySelector('#avatarDialog');
if (avatarDialog) {
  const fileInput = document.querySelector('#avatarFile');
  const canvas = document.querySelector('#avatarCanvas');
  const cropWrap = document.querySelector('#avatarCropWrap');
  const zoomInput = document.querySelector('#avatarZoom');
  const saveButton = document.querySelector('#saveAvatar');
  const feedback = document.querySelector('#avatarFeedback');
  const ctx = canvas.getContext('2d');
  let sourceImage = null;
  let pan = { x: 0, y: 0 };
  let pointerOrigin = null;
  const setFeedback = (message, error = false) => {
    feedback.textContent = message;
    feedback.classList.toggle('is-error', error);
  };
  const drawCrop = () => {
    if (!sourceImage) return;
    const side = Math.min(sourceImage.naturalWidth, sourceImage.naturalHeight) / Number(zoomInput.value);
    const scale = canvas.width / side;
    let sx = (sourceImage.naturalWidth - side) / 2 - pan.x / scale;
    let sy = (sourceImage.naturalHeight - side) / 2 - pan.y / scale;
    sx = Math.max(0, Math.min(sourceImage.naturalWidth - side, sx));
    sy = Math.max(0, Math.min(sourceImage.naturalHeight - side, sy));
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.beginPath(); ctx.arc(canvas.width / 2, canvas.height / 2, canvas.width / 2, 0, Math.PI * 2); ctx.clip();
    ctx.drawImage(sourceImage, sx, sy, side, side, 0, 0, canvas.width, canvas.height);
    ctx.restore();
  };
  const loadAvatarImage = (src) => {
    const image = new Image();
    image.onload = () => {
      sourceImage = image; pan = { x: 0, y: 0 }; zoomInput.value = '1';
      cropWrap.hidden = false; saveButton.disabled = false; setFeedback('Перетягніть фото та налаштуйте масштаб.'); drawCrop();
    };
    image.onerror = () => setFeedback('Не вдалося відкрити зображення.', true);
    image.src = src;
  };
  document.querySelectorAll('[data-open-avatar]').forEach(button => button.addEventListener('click', () => {
    setFeedback(''); fileInput.value = '';
    const existing = document.querySelector('[data-avatar-image]');
    if (existing?.src) loadAvatarImage(existing.src);
    else { sourceImage = null; cropWrap.hidden = true; saveButton.disabled = true; }
    avatarDialog.showModal();
  }));
  fileInput.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
      setFeedback('Потрібен файл JPG, PNG або WEBP розміром до 5 МБ.', true); fileInput.value = ''; return;
    }
    loadAvatarImage(URL.createObjectURL(file));
  });
  zoomInput.addEventListener('input', () => { pan = { x: 0, y: 0 }; drawCrop(); });
  canvas.addEventListener('pointerdown', event => {
    if (!sourceImage) return;
    pointerOrigin = { x: event.clientX - pan.x, y: event.clientY - pan.y };
    canvas.setPointerCapture(event.pointerId); canvas.classList.add('is-dragging');
  });
  canvas.addEventListener('pointermove', event => {
    if (!pointerOrigin) return;
    pan = { x: event.clientX - pointerOrigin.x, y: event.clientY - pointerOrigin.y }; drawCrop();
  });
  ['pointerup', 'pointercancel'].forEach(name => canvas.addEventListener(name, () => { pointerOrigin = null; canvas.classList.remove('is-dragging'); }));
  document.querySelector('[data-cancel-avatar]')?.addEventListener('click', () => avatarDialog.close());
  saveButton.addEventListener('click', async () => {
    if (!sourceImage) return;
    saveButton.disabled = true; setFeedback('Зберігаємо фото…');
    canvas.toBlob(async (blob) => {
      if (!blob) { setFeedback('Не вдалося підготувати фото.', true); saveButton.disabled = false; return; }
      const data = new FormData(); data.append('avatar', blob, 'avatar.jpg');
      try {
        const response = await fetch('/profile/avatar/', { method: 'POST', body: data, headers: { 'X-CSRFToken': document.querySelector('#avatarCsrf').value, 'X-Requested-With': 'XMLHttpRequest' } });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Не вдалося зберегти фото.');
        updateAvatarNodes(result); avatarDialog.close();
        document.querySelector('.profile-avatar-panel .toolbar-actions')?.classList.add('avatar-updated');
        showToast('Аватар оновлено');
      } catch (error) { setFeedback(error.message, true); saveButton.disabled = false; }
    }, 'image/jpeg', 0.92);
  });
  const updateAvatarNodes = ({ avatar_url: url, initial }) => {
    document.querySelectorAll('[data-avatar-root]').forEach(root => {
      let image = root.querySelector('[data-avatar-image]');
      let fallback = root.querySelector('[data-avatar-fallback]');
      if (url) {
        if (!image) { image = document.createElement('img'); image.dataset.avatarImage = ''; image.alt = ''; root.prepend(image); }
        image.src = `${url}?v=${Date.now()}`; image.classList.remove('avatar-image-enter'); void image.offsetWidth; image.classList.add('avatar-image-enter');
        if (fallback) fallback.hidden = true;
      } else {
        image?.remove(); if (fallback) { fallback.hidden = false; fallback.textContent = initial; }
      }
    });
    document.querySelectorAll('[data-delete-avatar]').forEach(button => button.hidden = !url);
  };
  document.querySelectorAll('[data-delete-avatar]').forEach(button => button.addEventListener('click', async () => {
    if (!window.confirm('Видалити фото профілю?')) return;
    button.disabled = true;
    try {
      const data = new FormData(); data.append('action', 'delete');
      const response = await fetch('/profile/avatar/', { method: 'POST', body: data, headers: { 'X-CSRFToken': document.querySelector('#avatarCsrf').value } });
      const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Не вдалося видалити фото.');
      updateAvatarNodes(result); showToast('Фото профілю видалено');
    } catch (error) { showToast(error.message); }
    finally { button.disabled = false; }
  }));
}

