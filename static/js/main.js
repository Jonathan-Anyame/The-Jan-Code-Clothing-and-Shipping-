// The Jan Code — UI interactions

document.addEventListener('DOMContentLoaded', function () {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    const navbar = document.getElementById('navbar');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function () {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });

        hamburger.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                hamburger.click();
            }
        });
    }

    document.querySelectorAll('.nav-menu a').forEach(function (link) {
        link.addEventListener('click', function () {
            if (navMenu) {
                navMenu.classList.remove('active');
                if (hamburger) hamburger.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    if (navbar) {
        const onScroll = function () {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    // Broken product images → gradient placeholder
    document.querySelectorAll('img.product-image, .product-card > img, .product-detail .product-image img').forEach(function (img) {
        img.addEventListener('error', function () {
            if (img.dataset.fallback) return;
            img.dataset.fallback = '1';
            const parent = img.parentElement;
            if (!parent) return;
            const placeholder = document.createElement('div');
            placeholder.className = 'product-image-placeholder';
            placeholder.innerHTML = '<i class="fas fa-box"></i>';
            img.replaceWith(placeholder);
        });
    });
});

function showToast(message, type) {
    type = type || 'success';
    const container = document.getElementById('toastContainer');
    if (!container) {
        alert(message);
        return;
    }
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(function () { toast.remove(); }, 300);
    }, 2800);
}

function addToCart(productId) {
    const qtyEl = document.getElementById('quantity');
    const quantity = qtyEl ? parseInt(qtyEl.value, 10) || 1 : 1;

    fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: quantity })
    })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
            if (res.d.success) {
                showToast('Added to cart', 'success');
            } else if (res.ok === false && res.d.message === 'Login required') {
                showToast('Please log in to add items', 'error');
                setTimeout(function () { window.location.href = '/login'; }, 900);
            } else {
                showToast(res.d.message || 'Could not add to cart', 'error');
            }
        })
        .catch(function () {
            showToast('Something went wrong', 'error');
        });
}

function removeItem(itemId) {
    fetch('/api/cart/remove/' + itemId, { method: 'DELETE' })
        .then(function (r) { return r.json(); })
        .then(function () {
            showToast('Item removed', 'success');
            setTimeout(function () { location.reload(); }, 400);
        })
        .catch(function () {
            showToast('Could not remove item', 'error');
        });
}

function completeOrder() {
    fetch('/api/order/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (d.success) {
                showToast('Order placed! Tracking: ' + d.tracking, 'success');
                setTimeout(function () { window.location.href = '/orders'; }, 1200);
            } else {
                showToast(d.message || 'Order failed', 'error');
            }
        })
        .catch(function () {
            showToast('Something went wrong', 'error');
        });
}
