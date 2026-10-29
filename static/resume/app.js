const authDialog = document.querySelector('#authDialog');
const templateDialog = document.querySelector('#templateDialog');
const toast = document.querySelector('.toast');
let toastTimer;

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

function setAuthMode(mode) {
  const signup = mode === 'signup';
  const form = document.querySelector('#authForm');
  if (!form) return;

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
  document.querySelector('#confirmPassword').hidden = !signup;
  form.elements.username.required = signup;
  form.elements.display_name.required = signup;
  form.elements.password2.required = signup;
  form.elements.password1.name = signup ? 'password1' : 'password';
}

document.addEventListener('click', (event) => {
  const authButton = event.target.closest('[data-open-auth]');
  if (authButton) {
    setAuthMode(authButton.dataset.openAuth);
    if (authDialog && !authDialog.open) authDialog.showModal();
    return;
  }

  const templateButton = event.target.closest('[data-template]');
  if (templateButton) {
    document.querySelector('#templateTitle').textContent =
      templateButton.dataset.template;
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
