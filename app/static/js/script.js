document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('shorten-form');
    const urlInput = document.getElementById('url-input');
    const shortenBtn = document.getElementById('shorten-btn');
    const resultContainer = document.getElementById('result-container');
    const shortUrlLink = document.getElementById('short-url');
    const copyBtn = document.getElementById('copy-btn');
    const downloadBtn = document.getElementById('download-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) return;

        // Show loading state
        shortenBtn.classList.add('loading');
        shortenBtn.disabled = true;
        resultContainer.classList.remove('visible');

        try {
            const formData = new FormData();
            formData.append('url', url);

            const response = await fetch('/shorten', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Display result
            const fullShortUrl = `${window.location.origin}/${data.short_code}`;
            shortUrlLink.href = fullShortUrl;
            shortUrlLink.textContent = fullShortUrl;

            // Handle Image Download Button
            if (data.is_image) {
                downloadBtn.classList.remove('hidden');
                downloadBtn.onclick = () => {
                    window.location.href = `/proxy-download?url=${encodeURIComponent(data.original_url)}`;
                };
            } else {
                downloadBtn.classList.add('hidden');
            }

            resultContainer.classList.remove('hidden');
            // Small delay to allow display:block to apply before opacity transition
            setTimeout(() => {
                resultContainer.classList.add('visible');
            }, 10);

        } catch (error) {
            console.error('Error:', error);
            alert('Something went wrong. Please try again.');
        } finally {
            shortenBtn.classList.remove('loading');
            shortenBtn.disabled = false;
        }
    });

    copyBtn.addEventListener('click', () => {
        const textToCopy = shortUrlLink.textContent;
        navigator.clipboard.writeText(textToCopy).then(() => {
            // Visual feedback
            const originalIcon = copyBtn.innerHTML;
            copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';

            setTimeout(() => {
                copyBtn.innerHTML = originalIcon;
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    });
});
