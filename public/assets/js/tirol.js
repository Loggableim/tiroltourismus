
/* ─── COUNTER ANIMATION ─── */
const counterObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if(entry.isIntersecting){
      const el = entry.target;
      const target = parseInt(el.dataset.count);
      if(!target) return;
      let current = 0;
      const step = Math.max(1, Math.floor(target / 60));
      const interval = setInterval(() => {
        current += step;
        if(current >= target) { current = target; clearInterval(interval); }
        el.textContent = current.toLocaleString();
      }, 20);
      counterObserver.unobserve(el);
    }
  });
}, { threshold: 0.5 });
document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));

/* ─── FAVORITE TOGGLE ─── */
const favBadge = document.getElementById('favBadge');
let favCount = 0;
document.querySelectorAll('.fav-btn, .accomm-fav').forEach(btn => {
  btn.addEventListener('click', function(e){
    e.preventDefault(); e.stopPropagation();
    this.classList.toggle('active');
    this.textContent = this.classList.contains('active') ? '♥' : '♡';
    favCount += this.classList.contains('active') ? 1 : -1;
    if(favCount > 0){ favBadge.textContent = favCount; favBadge.style.display = 'flex'; }
    else { favBadge.style.display = 'none'; }
  });
});

/* ─── BACK TO TOP ─── */
const bttBtn = document.getElementById('backToTop');
if(bttBtn){
  window.addEventListener('scroll', () => bttBtn.classList.toggle('visible', window.scrollY > 400));
  bttBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

/* ─── STICKY NAV ─── */
const mainNav = document.getElementById('mainNav');
if(mainNav) window.addEventListener('scroll', () => mainNav.classList.toggle('scrolled', window.scrollY > 0));

/* ─── SCROLL PROGRESS ─── */
const scrollProg = document.getElementById('scrollProgress');
if(scrollProg) window.addEventListener('scroll', () => {
  const h = document.documentElement;
  scrollProg.style.width = ((h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100) + '%';
});
