/**
 * Summary Detail Page - Interactive Citations
 * Handles clickable sentences and citation panel display
 */

document.addEventListener('DOMContentLoaded', function () {
    const citationDataEl = document.getElementById('citationData');
    if (!citationDataEl) return;

    const citationData = JSON.parse(citationDataEl.textContent);
    const citationPanel = document.getElementById('citationPanel');
    const citationContent = document.getElementById('citationContent');
    const closeCitations = document.getElementById('closeCitations');

    if (!citationPanel || !citationContent) return;

    // Handle sentence clicks
    document.querySelectorAll('.citable-sentence.has-sources').forEach(sentence => {
        sentence.addEventListener('click', function () {
            const citationId = this.dataset.citationId;
            const data = citationData[citationId];

            if (!data) return;

            // Remove active class from all sentences
            document.querySelectorAll('.citable-sentence').forEach(s => s.classList.remove('active'));

            // Add active class to clicked sentence
            this.classList.add('active');

            // Build citation HTML
            let html = '';
            data.sources.forEach((source, index) => {
                html += `
                    <div class="source-card">
                        <div class="source-quote">"${source.sentence}"</div>
                        <div class="source-meta">
                            ${source.expert_name ? `<span class="expert-name">— ${source.expert_name}</span>` : ''}
                            <span class="source-title">${source.article_source}</span>
                            <a href="${source.article_url}" target="_blank" class="full-article-link">Full Article →</a>
                        </div>
                    </div>
                `;
            });

            citationContent.innerHTML = html;
            citationPanel.classList.add('active');
        });
    });

    // Close panel
    if (closeCitations) {
        closeCitations.addEventListener('click', function () {
            citationPanel.classList.remove('active');
            document.querySelectorAll('.citable-sentence').forEach(s => s.classList.remove('active'));
        });
    }
});
