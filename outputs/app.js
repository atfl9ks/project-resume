const authDialog = document.querySelector('#authDialog');
const templateDialog = document.querySelector('#templateDialog');
const toast = document.querySelector('.toast');
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

function setAuthMode(mode) {
  const signup = mode === 'signup';
  document.querySelector('#dialogTitle').textContent = signup ? 'Почнімо з резюме' : 'Раді бачити знову';
  document.querySelector('#dialogCopy').textContent = signup ? 'Створи акаунт, щоб зберігати й редагувати свої резюме.' : 'Увійди, щоб продовжити роботу зі своїми резюме.';
  document.querySelector('#authSubmit').innerHTML = signup ? 'Створити акаунт <span>↗</span>' : 'Увійти <span>↗</span>';
  document.querySelector('#authSwitch').innerHTML = signup
    ? 'Вже маєш акаунт? <button type="button" data-open-auth="login">Увійти</button>'
    : 'Ще не маєш акаунта? <button type="button" data-open-auth="signup">Зареєструватися</button>';
  document.querySelector('#authForm').dataset.mode = mode;
  document.querySelector('#formSuccess').textContent = '';
}

document.addEventListener('click', (event) => {
  const authButton = event.target.closest('[data-open-auth]');
  if (authButton) {
    setAuthMode(authButton.dataset.openAuth);
    if (!authDialog.open) authDialog.showModal();
  }

  const templateButton = event.target.closest('[data-template]');
  if (templateButton) {
    document.querySelector('#templateTitle').textContent = templateButton.dataset.template;
    templateDialog.showModal();
  }

  if (event.target.matches('.dialog-close')) event.target.closest('dialog').close();
  if (event.target.matches('.choose-template')) {
    templateDialog.close();
    setAuthMode('signup');
    authDialog.showModal();
  }
});

document.querySelector('#authForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const mode = event.currentTarget.dataset.mode;
  document.querySelector('#formSuccess').textContent = mode === 'signup'
    ? 'Готово! Підключення акаунтів з’явиться після налаштування backend.'
    : 'Форма готова до підключення до системи автентифікації.';
});

document.querySelector('.menu-toggle').addEventListener('click', () => {
  const nav = document.querySelector('.main-nav');
  nav.classList.toggle('open');
  document.querySelector('.menu-toggle').setAttribute('aria-expanded', nav.classList.contains('open'));
});

document.querySelector('.main-nav').addEventListener('click', (event) => {
  if (event.target.closest('a')) document.querySelector('.main-nav').classList.remove('open');
});

document.querySelectorAll('a[href="#templates"]').forEach((link) => {
  link.addEventListener('click', () => {
    if (link.classList.contains('btn')) showToast('Обери шаблон, щоб переглянути його');
  });
});

[authDialog, templateDialog].forEach((dialog) => {
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
});
