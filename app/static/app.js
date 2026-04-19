(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const results = document.getElementById('helper-results');
    const searchInput = document.getElementById('helper-search');
    const categoryInput = document.getElementById('helper-category');

    const escapeHtml = (value) =>
      String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');

    const renderHelpers = (helpers) => {
      if (!results) return;
      if (!helpers.length) {
        results.innerHTML = '<div class="rounded-[2rem] border border-dashed border-slate-300 bg-white/85 p-8 text-center text-slate-500 md:col-span-2 xl:col-span-3">No helpers found.</div>';
        return;
      }

      results.innerHTML = helpers
        .map((helper) => {
          const photo = helper.profile_photo
            ? `<img src="/static/${escapeHtml(helper.profile_photo)}" alt="${escapeHtml(helper.full_name)}" class="h-full w-full object-cover">`
            : '<div class="flex h-full w-full items-center justify-center text-2xl">🧰</div>';
          return `
          <a href="/helpers/${helper.id}" class="group rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-glass backdrop-blur-xl transition hover:-translate-y-1">
            <div class="flex items-center gap-4">
              <div class="h-16 w-16 overflow-hidden rounded-2xl bg-slate-100">${photo}</div>
              <div>
                <div class="text-lg font-bold text-slate-950">${escapeHtml(helper.full_name)}</div>
                <div class="text-sm text-slate-500">${escapeHtml(helper.skill_category)} · ${escapeHtml(helper.city)}</div>
              </div>
            </div>
            <div class="mt-5 grid grid-cols-2 gap-3 text-sm text-slate-600">
              <div class="rounded-2xl bg-slate-50 p-3">⭐ ${helper.average_rating ?? 0}</div>
              <div class="rounded-2xl bg-slate-50 p-3">Jobs ${helper.completed_jobs ?? 0}</div>
              <div class="rounded-2xl bg-slate-50 p-3">₹${Math.round(helper.hourly_rate || 0)}/hr</div>
              <div class="rounded-2xl bg-slate-50 p-3">${helper.availability_on ? 'Available' : 'Offline'}</div>
            </div>
            <p class="mt-4 text-sm leading-6 text-slate-600">${escapeHtml((helper.short_bio || '').slice(0, 120))}${(helper.short_bio || '').length > 120 ? '...' : ''}</p>
          </a>
        `;
      })
      .join('');
  };
          `;
        })
        .join('');
    };
    const params = new URLSearchParams();
    const loadHelpers = async () => {
      if (!results || !window.LocalLifterSearch) return;

      const params = new URLSearchParams();
      if (searchInput && searchInput.value.trim()) params.set('q', searchInput.value.trim());
      if (categoryInput && categoryInput.value) params.set('category', categoryInput.value);
      const helpers = await response.json();
      results.classList.add('opacity-60');
      try {
        const response = await fetch(`${window.LocalLifterSearch.endpoint}?${params.toString()}`);
        const helpers = await response.json();
        renderHelpers(helpers);
      } catch (error) {
        results.innerHTML = '<div class="rounded-[2rem] border border-rose-200 bg-rose-50 p-8 text-center text-rose-700 md:col-span-2 xl:col-span-3">Unable to load helpers right now.</div>';
      } finally {
        results.classList.remove('opacity-60');
      }
    };
    debounceTimer = window.setTimeout(loadHelpers, 180);
    let debounceTimer = null;
    const triggerLoad = () => {
      window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(loadHelpers, 180);
    };
  if (results && window.LocalLifterSearch) {
    if (searchInput) searchInput.addEventListener('input', triggerLoad);
    if (categoryInput) categoryInput.addEventListener('change', loadHelpers);
})();
    if (results && window.LocalLifterSearch) {
      loadHelpers();
    }
  });