/**
 * PowersBioStrikes Landing Page JavaScript
 * Handles form submissions, navigation, and interactive elements
 */

(function() {
    'use strict';

    // ===== DOM Elements =====
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const heroForm = document.getElementById('hero-email-form');
    const footerForm = document.getElementById('footer-email-form');
    const foundingMemberForm = document.getElementById('founding-member-form');
    const navLinks = document.querySelectorAll('nav a[href^="#"]');

    // ===== Mobile Menu Toggle =====
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
            mobileMenu.classList.toggle('open');

            // Update aria-expanded for accessibility
            const isOpen = !mobileMenu.classList.contains('hidden');
            mobileMenuBtn.setAttribute('aria-expanded', isOpen);
        });

        // Close mobile menu when clicking a link
        mobileMenu.querySelectorAll('a').forEach(function(link) {
            link.addEventListener('click', function() {
                mobileMenu.classList.add('hidden');
                mobileMenu.classList.remove('open');
            });
        });
    }

    // ===== Smooth Scroll for Navigation =====
    navLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                const navHeight = document.querySelector('nav').offsetHeight;
                const targetPosition = targetElement.offsetTop - navHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ===== Email Form Handling =====
    function handleEmailSubmit(form, formName) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const emailInput = form.querySelector('input[type="email"]');
            const submitBtn = form.querySelector('button[type="submit"]');
            const email = emailInput.value.trim();

            // Validate email
            if (!isValidEmail(email)) {
                showToast('Please enter a valid email address', 'error');
                emailInput.focus();
                return;
            }

            // Show loading state
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span>';

            // Simulate API call (replace with actual endpoint)
            setTimeout(function() {
                // Store email locally for now (replace with actual API)
                storeEmail(email, formName);

                // Reset form
                emailInput.value = '';
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;

                // Show success message
                showToast('Thanks! You\'re on the list.', 'success');

            }, 1000);
        });
    }

    if (heroForm) handleEmailSubmit(heroForm, 'hero');
    if (footerForm) handleEmailSubmit(footerForm, 'footer');

    // ===== Founding Member Form Handling =====
    if (foundingMemberForm) {
        foundingMemberForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const nameInput = foundingMemberForm.querySelector('input[name="name"]');
            const emailInput = foundingMemberForm.querySelector('input[type="email"]');
            const submitBtn = foundingMemberForm.querySelector('button[type="submit"]');

            const name = nameInput ? nameInput.value.trim() : '';
            const email = emailInput.value.trim();

            // Validate email
            if (!isValidEmail(email)) {
                showToast('Please enter a valid email address', 'error');
                emailInput.focus();
                return;
            }

            // Show loading state
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Processing...';

            // Simulate API call (replace with actual endpoint)
            setTimeout(function() {
                // Store founding member locally
                storeFoundingMember(name, email);

                // Reset form
                if (nameInput) nameInput.value = '';
                emailInput.value = '';
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;

                // Update spots remaining counter
                updateSpotsRemaining();

                // Show success message
                showToast('Welcome to the Founding Members! Check your email for next steps.', 'success');

            }, 1500);
        });
    }

    // ===== Store Founding Member =====
    function storeFoundingMember(name, email) {
        const storedMembers = JSON.parse(localStorage.getItem('pbs_founding_members') || '[]');

        // Check for duplicates
        const isDuplicate = storedMembers.some(function(entry) {
            return entry.email === email;
        });

        if (!isDuplicate) {
            storedMembers.push({
                name: name,
                email: email,
                tier: 'founding_member',
                signupDate: new Date().toISOString(),
                freeMonthsRemaining: 6,
                status: 'active'
            });
            localStorage.setItem('pbs_founding_members', JSON.stringify(storedMembers));
        }

        console.log('Founding member captured:', name, email);
        console.log('Total founding members:', storedMembers.length);
    }

    // ===== Update Spots Remaining =====
    function updateSpotsRemaining() {
        const spotsElement = document.getElementById('spots-remaining');
        if (spotsElement) {
            const storedMembers = JSON.parse(localStorage.getItem('pbs_founding_members') || '[]');
            const totalSpots = 100;
            const remaining = Math.max(0, totalSpots - storedMembers.length);
            spotsElement.textContent = remaining;

            // Update progress bar if exists
            const progressBar = document.getElementById('spots-progress');
            if (progressBar) {
                const filledPct = ((totalSpots - remaining) / totalSpots) * 100;
                progressBar.style.width = filledPct + '%';
            }
        }
    }

    // Initialize spots counter on page load
    updateSpotsRemaining();

    // ===== Rolling Stats Ticker (Option C) =====
    const tickerStats = [
        { text: 'Last trade: <span class="text-green-400 font-semibold">INSM +141%</span>', type: 'win' },
        { text: 'Win rate: <span class="text-gold font-semibold">68.5%</span>', type: 'stat' },
        { text: 'Avg hold: <span class="text-gold font-semibold">47 days</span>', type: 'stat' },
        { text: 'Recent: <span class="text-green-400 font-semibold">CRNX +114%</span>', type: 'win' },
        { text: 'Recent loss: <span class="text-red-400 font-semibold">IMVT -75%</span>', type: 'loss' },
        { text: 'Active positions: <span class="text-gold font-semibold">17</span>', type: 'stat' },
        { text: 'Recent: <span class="text-green-400 font-semibold">VRNA +129%</span>', type: 'win' }
    ];

    let currentTickerIndex = 0;
    const tickerElement = document.querySelector('.stats-ticker');

    function updateTicker() {
        if (!tickerElement) return;

        const tickerItem = tickerElement.querySelector('.ticker-item');
        if (!tickerItem) return;

        // Fade out
        tickerItem.style.opacity = '0';
        tickerItem.style.transform = 'translateY(-10px)';

        setTimeout(function() {
            // Update content
            currentTickerIndex = (currentTickerIndex + 1) % tickerStats.length;
            tickerItem.innerHTML = tickerStats[currentTickerIndex].text;

            // Update pulse color based on type
            const pulse = tickerElement.parentElement.querySelector('.animate-pulse');
            if (pulse) {
                pulse.className = 'w-2 h-2 rounded-full mr-3 animate-pulse';
                if (tickerStats[currentTickerIndex].type === 'win') {
                    pulse.classList.add('bg-green-400');
                } else if (tickerStats[currentTickerIndex].type === 'loss') {
                    pulse.classList.add('bg-red-400');
                } else {
                    pulse.classList.add('bg-gold');
                }
            }

            // Fade in
            tickerItem.style.opacity = '1';
            tickerItem.style.transform = 'translateY(0)';
        }, 300);
    }

    // Add transition styles for ticker
    if (tickerElement) {
        const tickerItem = tickerElement.querySelector('.ticker-item');
        if (tickerItem) {
            tickerItem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            tickerItem.style.display = 'inline-block';
        }
        // Start the ticker rotation
        setInterval(updateTicker, 3000);
    }

    // ===== Email Validation =====
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // ===== Store Email (placeholder - replace with actual API) =====
    function storeEmail(email, source) {
        // Get existing emails from localStorage
        const storedEmails = JSON.parse(localStorage.getItem('pbs_waitlist') || '[]');

        // Check for duplicates
        const isDuplicate = storedEmails.some(function(entry) {
            return entry.email === email;
        });

        if (!isDuplicate) {
            storedEmails.push({
                email: email,
                source: source,
                timestamp: new Date().toISOString()
            });
            localStorage.setItem('pbs_waitlist', JSON.stringify(storedEmails));
        }

        // Log for debugging (remove in production)
        console.log('Email captured:', email, 'Source:', source);
        console.log('Total waitlist:', storedEmails.length);
    }

    // ===== Toast Notifications =====
    function showToast(message, type) {
        // Remove existing toasts
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.innerHTML = `
            <div class="flex items-center">
                <span class="mr-3">${type === 'success' ? '✓' : '!'}</span>
                <span>${message}</span>
            </div>
        `;

        // Add to DOM
        document.body.appendChild(toast);

        // Trigger animation
        setTimeout(function() {
            toast.classList.add('show');
        }, 10);

        // Remove after delay
        setTimeout(function() {
            toast.classList.remove('show');
            setTimeout(function() {
                toast.remove();
            }, 300);
        }, 4000);
    }

    // ===== Navbar Background on Scroll =====
    let lastScrollY = window.scrollY;
    const nav = document.querySelector('nav');

    window.addEventListener('scroll', function() {
        const currentScrollY = window.scrollY;

        // Add/remove background based on scroll position
        if (currentScrollY > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }

        // Hide/show nav on scroll direction (optional)
        if (currentScrollY > lastScrollY && currentScrollY > 200) {
            nav.style.transform = 'translateY(-100%)';
        } else {
            nav.style.transform = 'translateY(0)';
        }

        lastScrollY = currentScrollY;
    });

    // ===== Intersection Observer for Animations =====
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all cards and sections
    document.querySelectorAll('.premium-card, section > div').forEach(function(el) {
        el.classList.add('animate-ready');
        observer.observe(el);
    });

    // ===== Add Animation Styles =====
    const style = document.createElement('style');
    style.textContent = `
        .animate-ready {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .animate-in {
            opacity: 1;
            transform: translateY(0);
        }
        nav {
            transition: transform 0.3s ease, background-color 0.3s ease;
        }
        nav.scrolled {
            background-color: rgba(28, 28, 28, 0.98);
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    // ===== Track Record Data (placeholder) =====
    // This would be replaced with actual API calls to fetch track record
    const trackRecordData = {
        trades: [],
        summary: {
            totalTrades: 0,
            winRate: 0,
            avgReturn: 0
        }
    };

    // ===== Console Easter Egg =====
    console.log('%c PowersBioStrikes ', 'background: #D4AF37; color: #1C1C1C; font-size: 24px; font-weight: bold; padding: 10px 20px;');
    console.log('%c Systematic. Quantitative. Transparent. ', 'color: #D4AF37; font-size: 14px;');
    console.log('%c Looking for trading opportunities? Join the waitlist! ', 'color: #888; font-size: 12px;');

})();
