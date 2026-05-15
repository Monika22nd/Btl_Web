(function () {
  const toastHost = document.getElementById("toast-host");

  function toast(message) {
    if (!toastHost) return;
    const node = document.createElement("div");
    node.className = "toast";
    node.textContent = message;
    toastHost.appendChild(node);
    window.setTimeout(() => node.remove(), 2600);
  }

  document.querySelectorAll("[data-carousel]").forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll(".hero-slide"));
    const dotHost = carousel.querySelector("[data-carousel-dots]");
    let active = 0;
    let timer = null;

    function render(next) {
      active = next;
      slides.forEach((slide, index) => slide.classList.toggle("is-active", index === active));
      if (dotHost) {
        Array.from(dotHost.children).forEach((dot, index) => dot.classList.toggle("is-active", index === active));
      }
    }

    if (dotHost) {
      slides.forEach((_, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.setAttribute("aria-label", `Chuyển banner ${index + 1}`);
        button.addEventListener("click", () => render(index));
        dotHost.appendChild(button);
      });
    }

    function start() {
      timer = window.setInterval(() => render((active + 1) % slides.length), 4000);
    }

    if (slides.length > 1) {
      render(0);
      start();
      carousel.addEventListener("mouseenter", () => window.clearInterval(timer));
      carousel.addEventListener("mouseleave", start);
    }
  });

  document.querySelectorAll("[data-qty-minus], [data-qty-plus]").forEach((button) => {
    button.addEventListener("click", () => {
      const control = button.closest(".qty-control");
      const input = control ? control.querySelector("input[type='number']") : null;
      if (!input) return;
      const step = button.hasAttribute("data-qty-plus") ? 1 : -1;
      const min = Number(input.min || 1);
      input.value = Math.max(min, Number(input.value || min) + step);
    });
  });

  document.querySelectorAll("[data-add-cart]").forEach((button) => {
    button.addEventListener("click", () => {
      toast("Đã thêm vào giỏ hàng");
    });
  });
})();
