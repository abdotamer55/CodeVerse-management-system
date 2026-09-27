/**
 * CodeVerse PWA — Install & Registration
 * Handles service worker registration, install prompt, and update notifications.
 */

(function () {
  'use strict';

  // ─── Service Worker Registration ───────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
      try {
        const reg = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
        });
        console.log('[PWA] Service Worker registered, scope:', reg.scope);

        // Check for updates every hour
        setInterval(() => reg.update(), 60 * 60 * 1000);

        // Notify user when new version is available
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              showUpdateBanner();
            }
          });
        });
      } catch (err) {
        console.warn('[PWA] Service Worker registration failed:', err);
      }
    });
  }

  // ─── Install Prompt (Add to Home Screen) ─────────────────────────────────
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;

    // Only show banner if user hasn't dismissed it before
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (!dismissed) {
      // Show after short delay so page loads first
      setTimeout(() => showInstallBanner(), 2500);
    }
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    hideInstallBanner();
    localStorage.setItem('pwa-install-dismissed', '1');
    console.log('[PWA] App installed successfully!');
  });

  // ─── Install Banner UI ─────────────────────────────────────────────────────
  function showInstallBanner() {
    if (document.getElementById('pwa-install-banner')) return;

    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'تثبيت التطبيق');
    banner.innerHTML = `
      <div class="pwa-banner-inner">
        <img src="/static/icons/icon-72x72.png" alt="كودفيرس" class="pwa-icon" />
        <div class="pwa-text">
          <strong>ثبّت تطبيق كودفيرس</strong>
          <span>على شاشتك الرئيسية للوصول السريع بدون متصفح</span>
        </div>
        <div class="pwa-actions">
          <button id="pwa-install-btn" class="pwa-btn-install">تثبيت</button>
          <button id="pwa-dismiss-btn" class="pwa-btn-dismiss" aria-label="إغلاق">✕</button>
        </div>
      </div>
    `;

    // Inject styles
    if (!document.getElementById('pwa-banner-styles')) {
      const style = document.createElement('style');
      style.id = 'pwa-banner-styles';
      style.textContent = `
        #pwa-install-banner {
          position: fixed;
          bottom: 1rem;
          left: 1rem;
          right: 1rem;
          z-index: 9999;
          animation: pwa-slide-up 0.4s cubic-bezier(.16,1,.3,1);
        }
        @keyframes pwa-slide-up {
          from { transform: translateY(120%); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
        .pwa-banner-inner {
          display: flex;
          align-items: center;
          gap: 12px;
          background: #1e293b;
          border: 1px solid rgba(99,102,241,0.35);
          border-radius: 16px;
          padding: 14px 16px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.15);
          backdrop-filter: blur(12px);
          max-width: 480px;
          margin: 0 auto;
          direction: rtl;
        }
        .pwa-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          flex-shrink: 0;
        }
        .pwa-text {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .pwa-text strong {
          color: #e2e8f0;
          font-size: 0.95rem;
          font-weight: 700;
          font-family: Cairo, sans-serif;
        }
        .pwa-text span {
          color: #94a3b8;
          font-size: 0.78rem;
          font-family: Tajawal, sans-serif;
          line-height: 1.4;
        }
        .pwa-actions {
          display: flex;
          gap: 8px;
          align-items: center;
          flex-shrink: 0;
        }
        .pwa-btn-install {
          background: linear-gradient(135deg, #6366f1, #4f46e5);
          color: #fff;
          border: none;
          border-radius: 10px;
          padding: 8px 18px;
          font-family: Cairo, sans-serif;
          font-size: 0.88rem;
          font-weight: 700;
          cursor: pointer;
          transition: opacity .2s;
        }
        .pwa-btn-install:hover { opacity: 0.9; }
        .pwa-btn-dismiss {
          background: transparent;
          border: none;
          color: #64748b;
          font-size: 1.1rem;
          cursor: pointer;
          padding: 4px 6px;
          border-radius: 6px;
          line-height: 1;
          transition: color .2s;
        }
        .pwa-btn-dismiss:hover { color: #e2e8f0; }

        /* iOS Safari install hint */
        #pwa-ios-hint {
          position: fixed;
          bottom: 1rem;
          left: 1rem;
          right: 1rem;
          z-index: 9999;
          background: #1e293b;
          border: 1px solid rgba(99,102,241,0.35);
          border-radius: 16px;
          padding: 14px 16px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.5);
          max-width: 480px;
          margin: 0 auto;
          direction: rtl;
          text-align: center;
          animation: pwa-slide-up 0.4s cubic-bezier(.16,1,.3,1);
        }
        #pwa-ios-hint p {
          color: #94a3b8;
          font-size: 0.85rem;
          font-family: Tajawal, sans-serif;
          margin: 6px 0;
          line-height: 1.6;
        }
        #pwa-ios-hint strong { color: #e2e8f0; }
        #pwa-ios-hint .pwa-close-ios {
          background: transparent;
          border: 1px solid rgba(255,255,255,0.15);
          color: #94a3b8;
          border-radius: 8px;
          padding: 6px 14px;
          cursor: pointer;
          font-family: Cairo, sans-serif;
          font-size: 0.8rem;
          margin-top: 8px;
        }

        /* Update banner */
        #pwa-update-banner {
          position: fixed;
          top: 1rem;
          left: 1rem;
          right: 1rem;
          z-index: 9999;
          background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(16,185,129,0.1));
          border: 1px solid rgba(99,102,241,0.4);
          border-radius: 12px;
          padding: 12px 16px;
          display: flex;
          align-items: center;
          gap: 12px;
          max-width: 480px;
          margin: 0 auto;
          direction: rtl;
          box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        #pwa-update-banner span { color: #e2e8f0; font-size: 0.88rem; flex: 1; font-family: Tajawal, sans-serif; }
        #pwa-update-banner button {
          background: #6366f1;
          color: #fff;
          border: none;
          border-radius: 8px;
          padding: 6px 14px;
          cursor: pointer;
          font-family: Cairo, sans-serif;
          font-size: 0.82rem;
        }
      `;
      document.head.appendChild(style);
    }

    document.body.appendChild(banner);

    document.getElementById('pwa-install-btn').addEventListener('click', async () => {
      if (!deferredPrompt) return;
      await deferredPrompt.prompt();
      const result = await deferredPrompt.userChoice;
      if (result.outcome === 'accepted') {
        console.log('[PWA] User accepted install');
      }
      deferredPrompt = null;
      hideInstallBanner();
    });

    document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
      hideInstallBanner();
      localStorage.setItem('pwa-install-dismissed', '1');
    });
  }

  function hideInstallBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.style.animation = 'none';
      banner.style.transform = 'translateY(120%)';
      banner.style.transition = 'transform 0.3s ease';
      setTimeout(() => banner.remove(), 300);
    }
  }

  // ─── iOS Safari Install Hint ───────────────────────────────────────────────
  function isIOS() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent);
  }

  function isInStandaloneMode() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }

  if (isIOS() && !isInStandaloneMode()) {
    const iosDismissed = localStorage.getItem('pwa-ios-dismissed');
    if (!iosDismissed) {
      setTimeout(() => {
        const hint = document.createElement('div');
        hint.id = 'pwa-ios-hint';
        hint.innerHTML = `
          <strong>📱 ثبّت كودفيرس على آيفون</strong>
          <p>
            اضغط على زر المشاركة
            <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='%236366f1'%3E%3Cpath d='M16 5l-1.42 1.42-1.59-1.59V16h-1.98V4.83L9.42 6.42 8 5l4-4 4 4zm4 5v11c0 1.1-.9 2-2 2H6c-1.11 0-2-.89-2-2V10c0-1.11.89-2 2-2h3v2H6v11h12V10h-3V8h3c1.1 0 2 .89 2 2z'/%3E%3C/svg%3E"
            style="vertical-align:middle;margin:0 3px" />
            ثم اختر <strong>"إضافة إلى الشاشة الرئيسية"</strong>
          </p>
          <button class="pwa-close-ios" onclick="document.getElementById('pwa-ios-hint').remove();localStorage.setItem('pwa-ios-dismissed','1')">
            فهمت
          </button>
        `;
        document.body.appendChild(hint);
      }, 3000);
    }
  }

  // ─── Update Banner ─────────────────────────────────────────────────────────
  function showUpdateBanner() {
    if (document.getElementById('pwa-update-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'pwa-update-banner';
    banner.innerHTML = `
      <span>🚀 يوجد تحديث جديد لتطبيق كودفيرس!</span>
      <button onclick="window.location.reload()">تحديث الآن</button>
    `;
    document.body.prepend(banner);
  }

})();
