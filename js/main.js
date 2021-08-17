/*To show hidden things */
const navMenu = document.getElementById('nav-menu'),
      toggleMenu = document.getElementById('nav-toggle'),
      closeMenu = document.getElementById('nav-close')

/* show */
toggleMenu.addEventListener('click', ()=>{
        navMenu.classList.toggle('show')
})


/* hidden */
closeMenu.addEventListener('click',()=>{
    navMenu.classList.remove('show')
})

/*Remove Menu*/
const navLink = document.querySelectorAll('.nav__link');

function linkAction(){
  navMenu.classList.remove('show')
}
navLink.forEach(element => {
  element.addEventListener('click',linkAction)
});

/* scroll sections active link */
const sections = document.querySelectorAll('section[id]')

window.addEventListener('scroll', scrollActive)

function scrollActive(){
  const scrollY = window.pageYOffset

  sections.forEach(curr => {
           const sectionHeight = curr.offsetHeight
           const sectionTop = curr.offsetTop - 50
           sectionId = curr.getAttribute('id')

           if(scrollY > sectionTop  && scrollY <= sectionTop + sectionHeight){
             document.querySelector('.nav_menu a[href*='+ sectionId +']').classList.add('active');
           }else{
            document.querySelector('.nav_menu a[href*='+ sectionId +']').classList.remove('active');
           }
  });
}