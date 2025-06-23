  setTimeout(() => {
    const alerts = document.querySelectorAll('.alert:not(.persistent-alert)');
    alerts.forEach(alert => {
      alert.classList.remove('show');
      alert.classList.add('fade-out');
      setTimeout(() => alert.remove(), 500);
    });
  }, 4000);

