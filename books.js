// The library. Add one entry per book.
//
//   title   (required)
//   author  (optional) leave out for books like a Bible
//   isbn    (optional) shows the cover from Open Library when one exists
//   series  (optional) e.g. "Elephant & Piggie"
//   notes   (optional) e.g. "board book", "signed copy"
//
// Keep each entry wrapped in { } and separated by commas.
const BOOKS = [
  { title: "Goodnight Moon", author: "Margaret Wise Brown", isbn: "9780064430173" },
  { title: "The Very Hungry Caterpillar", author: "Eric Carle", isbn: "9780399226908", notes: "board book" },
  { title: "Where the Wild Things Are", author: "Maurice Sendak", isbn: "9780060254926" },
  { title: "Adventure Bible for Early Readers", isbn: "9780310727422", cover: "covers/9780310727422.jpg" },
];
