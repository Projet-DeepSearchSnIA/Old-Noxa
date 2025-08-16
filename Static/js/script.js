const dropdownMenu = document.querySelector(".dropdown-menu");
const dropdownButton = document.querySelector(".dropdown-button");

if (dropdownButton) {
  dropdownButton.addEventListener("click", () => {
    dropdownMenu.classList.toggle("show");
  });
}

document.querySelectorAll(".toast-message").forEach((toast) => {
    const closeBtn = toast.querySelector(".close-btn");

    // Manual close
    closeBtn.addEventListener("click", () => {
        toast.remove();
    });

    // Auto close after timeout
    const timeout = parseInt(toast.dataset.timeout, 10) || 2000;
    setTimeout(() => {
        toast.remove();
    }, timeout);
});

const closeBtn = document.querySelector(".modal__header .close_btn");
const cancelBtn = document.querySelector(".cancel");
const modal = document.querySelector(".modal_cont");

const newCollBtn = document.querySelector(".profile__container--favs__item--collections__newcol");

const addToCollectionBtn = document.querySelector(".add_to_collection_btn") // add to collection btn #publication.html

if (closeBtn) {
  closeBtn.addEventListener('click', () => {
    modal.classList.remove("show")
  });
}

if (cancelBtn) {
  cancelBtn.addEventListener('click', () => {
    modal.classList.remove("show")
  });
}

if (newCollBtn) {
  newCollBtn.addEventListener('click', () => {
    modal.classList.toggle("show")
  });
}

if (addToCollectionBtn) {
  addToCollectionBtn.addEventListener('click', () => {
    modal.classList.toggle("show")
  });
}

document.addEventListener('DOMContentLoaded', function () {
    const createResizableTable = function (table) {
        const cols = table.querySelectorAll('th');
        [].forEach.call(cols, function (col) {
            // Add a resizer element to the column
            const resizer = document.createElement('div')
            resizer.classList.add('resizer')

            // Set the height
            resizer.style.height = (table.offsetHeight - 3) + 'px'

            col.appendChild(resizer)

            createResizableColumn(col, resizer)
        })
    }

    const createResizableColumn = function (col, resizer) {
        let x = 0
        let w = 0

        const mouseDownHandler = function (e) {
            x = e.clientX

            const styles = window.getComputedStyle(col)
            w = parseInt(styles.width, 10)

            document.addEventListener('mousemove', mouseMoveHandler)
            document.addEventListener('mouseup', mouseUpHandler)

            resizer.classList.add('resizing')
        }

        const mouseMoveHandler = function (e) {
            const dx = e.clientX - x
            col.style.width = (w + dx) + 'px'
        }

        const mouseUpHandler = function () {
            resizer.classList.remove('resizing')
            document.removeEventListener('mousemove', mouseMoveHandler)
            document.removeEventListener('mouseup', mouseUpHandler)
        }

        resizer.addEventListener('mousedown', mouseDownHandler)
    }

    createResizableTable(document.getElementById('resizable'))
})






