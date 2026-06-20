const menuToggle = document.getElementById("menuToggle");
const mainNav = document.getElementById("mainNav");
const siteHeader = document.getElementById("siteHeader");

if (menuToggle) {
  menuToggle.addEventListener("click", () => {
    mainNav.classList.toggle("open");
  });
}

window.addEventListener("scroll", () => {
  if (window.scrollY > 30) {
    siteHeader.classList.add("scrolled");
  } else {
    siteHeader.classList.remove("scrolled");
  }
});

const reveals = document.querySelectorAll(".reveal");

function revealOnScroll() {
  reveals.forEach((item) => {
    const top = item.getBoundingClientRect().top;
    const windowHeight = window.innerHeight;
    if (top < windowHeight - 80) {
      item.classList.add("active");
    }
  });
}

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);