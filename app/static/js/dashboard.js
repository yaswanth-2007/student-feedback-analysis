/**
 * Analytics Dashboard Chart.js Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check if dashboard canvas elements exist
    const courseChartEl = document.getElementById('courseRatingChart');
    const distChartEl = document.getElementById('ratingDistributionChart');
    const questionChartEl = document.getElementById('questionRatingChart');
    const trendChartEl = document.getElementById('submissionTrendChart');

    if (!courseChartEl || !distChartEl) return;

    // Palette tokens
    const primaryIndigo = '#4F46E5';
    const indigoLight = 'rgba(79, 70, 229, 0.2)';
    const emerald = '#10B981';
    const amber = '#F59E0B';
    const red = '#EF4444';
    const blue = '#3B82F6';

    // Global Chart.js defaults
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.color = '#64748B';

    // 1. Course Average Rating (Horizontal Bar Chart)
    const rawCourseLabels = JSON.parse(courseChartEl.getAttribute('data-labels') || '[]');
    const rawCourseAverages = JSON.parse(courseChartEl.getAttribute('data-averages') || '[]');

    new Chart(courseChartEl, {
        type: 'bar',
        data: {
            labels: rawCourseLabels.length ? rawCourseLabels : ['No Course Data'],
            datasets: [{
                label: 'Mean Rating (out of 5.0)',
                data: rawCourseAverages.length ? rawCourseAverages : [0],
                backgroundColor: primaryIndigo,
                borderRadius: 4,
                barThickness: 16
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1 },
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Average: ${ctx.parsed.x ? ctx.parsed.x.toFixed(2) : 'No responses'} / 5.00`
                    }
                }
            }
        }
    });

    // 2. Rating Distribution (1 through 5 Bar Chart)
    const rawDistLabels = ['1 - Poor', '2 - Below Avg', '3 - Average', '4 - Good', '5 - Excellent'];
    const rawDistCounts = JSON.parse(distChartEl.getAttribute('data-counts') || '[0,0,0,0,0]');

    new Chart(distChartEl, {
        type: 'bar',
        data: {
            labels: rawDistLabels,
            datasets: [{
                label: 'Responses Count',
                data: rawDistCounts,
                backgroundColor: [red, amber, '#FBBF24', blue, emerald],
                borderRadius: 6,
                maxBarThickness: 44
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: '#E2E8F0' }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Evaluations: ${ctx.parsed.y}`
                    }
                }
            }
        }
    });

    // 3. Question-wise Average Rating (Bar Chart)
    if (questionChartEl) {
        const rawQuesLabels = JSON.parse(questionChartEl.getAttribute('data-labels') || '[]');
        const rawQuesAverages = JSON.parse(questionChartEl.getAttribute('data-averages') || '[]');

        new Chart(questionChartEl, {
            type: 'bar',
            data: {
                labels: rawQuesLabels.length ? rawQuesLabels : ['No Question Data'],
                datasets: [{
                    label: 'Question Mean Score',
                    data: rawQuesAverages.length ? rawQuesAverages : [0],
                    backgroundColor: '#6366F1',
                    borderRadius: 4,
                    maxBarThickness: 36
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 5,
                        ticks: { stepSize: 1 },
                        grid: { color: '#E2E8F0' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            callback: function(val, index) {
                                const label = this.getLabelForValue(val);
                                return label.length > 25 ? label.substr(0, 22) + '...' : label;
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Mean Score: ${ctx.parsed.y ? ctx.parsed.y.toFixed(2) : 'N/A'} / 5.00`
                        }
                    }
                }
            }
        });
    }

    // 4. Feedback Submissions Over Time (Line Chart)
    if (trendChartEl) {
        // Fetch dynamic trend data from API
        const courseFilter = trendChartEl.getAttribute('data-course-id') || '';
        const startDate = trendChartEl.getAttribute('data-start-date') || '';
        const endDate = trendChartEl.getAttribute('data-end-date') || '';

        const url = `/api/admin/analytics/trends?course_id=${courseFilter}&start_date=${startDate}&end_date=${endDate}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                const labels = data.labels && data.labels.length ? data.labels : ['No Activity'];
                const counts = data.counts && data.counts.length ? data.counts : [0];

                new Chart(trendChartEl, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Daily Submissions',
                            data: counts,
                            borderColor: primaryIndigo,
                            backgroundColor: indigoLight,
                            fill: true,
                            tension: 0.35,
                            pointRadius: 3,
                            pointHoverRadius: 6,
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { precision: 0 },
                                grid: { color: '#E2E8F0' }
                            },
                            x: {
                                grid: { display: false }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` Submissions: ${ctx.parsed.y}`
                                }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error('Error fetching trend analytics:', err));
    }
});
