const fetchBtn = document.getElementById('fetchBtn');
const btnText = document.getElementById('btnText');
const loader = document.getElementById('loader');
const titleEl = document.getElementById('title');
const dateEl = document.getElementById('date');
const card = document.getElementById('result');
const placeholder = document.getElementById('placeholder');

if (fetchBtn) {
    fetchBtn.addEventListener('click', async () => {
        // UI State: Loading
        fetchBtn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';
        card.classList.remove('show');

        try {
            const response = await fetch('/api/latest/');
            const data = await response.json();

            if (response.ok) {
                setTimeout(() => {
                    placeholder.style.display = 'none';
                    titleEl.textContent = data.title;
                    dateEl.textContent = 'Published: ' + data.published_at;
                    card.classList.add('show');

                    // Reset button
                    fetchBtn.disabled = false;
                    btnText.style.display = 'inline';
                    loader.style.display = 'none';
                }, 600); // Small delay for smooth feel
            } else {
                alert('Error: ' + data.error);
                resetButton();
            }
        } catch (err) {
            alert('Connection failed');
            resetButton();
        }
    });

    function resetButton() {
        fetchBtn.disabled = false;
        btnText.style.display = 'inline';
        loader.style.display = 'none';
    }
}
