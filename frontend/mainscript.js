(function() {
    'use strict';
    var filtersBtn = document.getElementById('filters-btn');
    var filtersOverlay = document.getElementById('filters-overlay');
    var applyFiltersBtn = document.getElementById('apply-filters-btn');
    var reportBtn = document.getElementById('report-btn');
    var navButtons = document.querySelectorAll('.nav-btn');
    var tabSections = document.querySelectorAll('.tab-content');
    var distanceInput = document.getElementById('distance');
    var distanceSpan = document.getElementById('distance-value');

    function openModal() {
        filtersOverlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
    function closeModal() {
        filtersOverlay.classList.add('hidden');
        document.body.style.overflow = '';
    }

    if (filtersBtn) filtersBtn.addEventListener('click', openModal);
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            var ageMin = document.getElementById('age-min').value;
            var ageMax = document.getElementById('age-max').value;
            var gender = document.querySelector('input[name="gender"]:checked');
            var distance = distanceInput ? distanceInput.value : '25';
            console.log('Filters applied:', { ageMin, ageMax, gender: gender ? gender.value : 'everyone', distance });
            closeModal();
        });
    }
    if (filtersOverlay) {
        filtersOverlay.addEventListener('click', function(e) {
            if (e.target === filtersOverlay) closeModal();
        });
    }
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && filtersOverlay && !filtersOverlay.classList.contains('hidden')) {
            closeModal();
        }
    });

    if (reportBtn) {
        reportBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to report this profile?')) {
                alert('Thank you. Your report has been submitted.');
            }
        });
    }

    if (distanceInput && distanceSpan) {
        distanceInput.addEventListener('input', function() {
            distanceSpan.textContent = this.value;
        });
    }

    navButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var targetId = btn.getAttribute('data-tab');
            if (!targetId) return;
            var targetSection = document.getElementById(targetId);
            if (!targetSection) return;
            tabSections.forEach(function(section) {
                section.classList.add('hidden');
            });
            targetSection.classList.remove('hidden');
            navButtons.forEach(function(b) {
                b.classList.remove('active');
            });
            btn.classList.add('active');
        });
    });
})();