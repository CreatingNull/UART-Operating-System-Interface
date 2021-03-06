/** When the user scrolls the page check if navbar needs to stick. */
window.onscroll = function () {
  stickNavbar();
};

/** Toggles the responsive class on nav when user clicks on icon. */
function dynamicNavigation() {
  const nav = document.getElementById('top-navigation');
  if (nav.classList.contains('responsive')) {
    nav.classList.remove('responsive');
  } else {
    nav.classList.add('responsive');
  }
}

/** Adds the sticky class once scroll passes threshold. */
function stickNavbar() {
  const navbar = document.getElementById('top-navigation'); // Get the navbar
  const stickyHeight = navbar.offsetTop; // Get the nav offset position
  if (window.pageYOffset > stickyHeight) {
    navbar.classList.add('sticky');
  } else {
    navbar.classList.remove('sticky');
  }
}

/**
 * Go to tab by name.
 * @param {object} tab Header button object.
 * */
function switchTab(tab) {
  const tabHeaders = tab.parentElement.getElementsByClassName('tab-nav-links');
  const tabs = tab.parentElement.parentElement.getElementsByClassName(
    'tab-nav-content',
  );
  for (let i = 0; i < tabHeaders.length; i++) {
    if (tabHeaders[i] === tab && !tabHeaders[i].classList.contains('active')) {
      tabHeaders[i].classList.add('active');
      tabs[i].classList.add('active');
    } else if (
      tabHeaders[i] !== tab &&
      tabHeaders[i].classList.contains('active')
    ) {
      tabHeaders[i].classList.remove('active');
      tabs[i].classList.remove('active');
    }
  }
}
