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
  { title: "Adventure Bible for Early Readers", isbn: "9780310727422", cover: "covers/9780310727422.jpg" },
  { title: "Corduroy", author: "Don Freeman", isbn: "9780670241330", cover: "covers/9780670241330.jpg" },
  { title: "If You Give a Mouse a Cookie", author: "Laura Joffe Numeroff", isbn: "9780060245863", cover: "covers/9780060245863.jpg" },
  { title: "Little Whale", isbn: "9781836505099", cover: "covers/9781836505099.jpg" },
  { title: "You're My Little Cutie Pie", author: "Natalie Marshall, Nicola Edwards", isbn: "9781667204598", cover: "covers/9781667204598.jpg" },
  { title: "Spot goes to the farm", author: "Eric Hill", isbn: "9780399236471", cover: "covers/9780399236471.jpg" },
  { title: "I'll Love You till the Cows Come Home", author: "Kathryn Cristaldi, Kristyna Litten", isbn: "9780063295971", cover: "covers/9780063295971.jpg" },
  { title: "Brown Bear, Brown Bear, What Do You See?", author: "Bill Martin Jr., Eric Carle", isbn: "9780805047905", cover: "covers/9780805047905.jpg" },
  { title: "Chicka Chicka Boom Boom", author: "Bill Martin Jr., John Archambault", isbn: "9781442450707", cover: "covers/9781442450707.jpg" },
  { title: "The Rainbow Fish", author: "Marcus Pfister", isbn: "9781558585362", cover: "covers/9781558585362.jpg" },
  { title: "Have You Seen My Duckling?", author: "Nancy Tafuri", isbn: "9780688148997", cover: "covers/9780688148997.jpg" },
  { title: "Where's Spot?", author: "Eric Hill", isbn: "9780399240461", cover: "covers/9780399240461.jpg" },
  { title: "Goodnight Moon", author: "Margaret Wise Brown", isbn: "9780063111318", cover: "covers/9780063111318.jpg" },
  { title: "First look and find Sesame Street Elmo & friends", author: "DiCicco Studios", isbn: "9781412730761", cover: "covers/9781412730761.jpg" },
  { title: "You're My Little Sunshine", author: "Natalie Marshall", isbn: "9781645178859", cover: "covers/9781645178859.jpg" },
  { title: "Who Is in the Garden?", author: "Simon Abbott, Simon Abbot", isbn: "9781441335678", cover: "covers/9781441335678.jpg" },
  { title: "Teddy Bears' Picnic", author: "Jimmy Kennedy", isbn: "9780689835308", cover: "covers/9780689835308.jpg" },
  { title: "Great & Small Prayers for Babies", author: "Pamela Kennedy, Anna Abramskaya", isbn: "9781535948210", cover: "covers/9781535948210.jpg" },
  { title: "Baby loves coding!", author: "Ruth Spiro", isbn: "9781580898843", cover: "covers/9781580898843.jpg" },
  { title: "Get Dressed, Belly Button!", author: "Lucie Brunellière", isbn: "9798765663523", cover: "covers/9798765663523.jpg" },
  { title: "The Very Hungry Caterpillar", author: "Eric Carle", isbn: "9780399226908", cover: "covers/9780399226908.jpg" },
  { title: "My First Black and White Book: Play!", author: "Pascale Estellon", isbn: "9798895090190", cover: "covers/9798895090190.jpg" },
  { title: "Baby Bear's Busy Day with Brown Bear and Friends", author: "Odd Dot, Eric Carle", isbn: "9781250875679", cover: "covers/9781250875679.jpg" },
  { title: "Baby's First Blessings", author: "Caroline Silva, Gail Yerrill", isbn: "9781966969235", cover: "covers/9781966969235.jpg" },
  { title: "My Mom and Me", author: "Penny Johnson, Kirsten Irving", cover: "covers/my-mom-and-me.jpg" },
//  { title: "Bright Baby Touch & Feel Slipcase", author: "Roger Priddy", isbn: "9780312498726", cover: "covers/9780312498726.jpg" },
  { title: "On the Farm", author: "Priddy Books Staff", isbn: "9780312498597", cover: "covers/9780312498597.jpg" },
  { title: "Baby Animals", author: "Priddy Books Staff", isbn: "9780312498580", cover: "covers/9780312498580.jpg" },
  { title: "At the Zoo", author: "Priddy Books Staff", isbn: "9780312498573", cover: "covers/9780312498573.jpg" },
  { title: "Perfect Pets", author: "Priddy Books Staff", isbn: "9780312498603", cover: "covers/9780312498603.jpg" },
  { title: "Computer Engineering for Big Babies", author: "Chase Roberts", isbn: "9781735208749", cover: "covers/9781735208749.jpg" },
  { title: "Computer Engineering for Babies", author: "Chase Roberts", cover: "covers/computer-engineering-for-babies.jpg" },
  { title: "Talking like the rain", author: "X. J. Kennedy, Dorothy M. Kennedy, Jane Dyer", isbn: "9780316488891", cover: "covers/9780316488891.jpg" },
  { title: "Carl goes shopping", author: "Alexandra Day", isbn: "9780374311018", cover: "covers/9780374311018.jpg" },
];
