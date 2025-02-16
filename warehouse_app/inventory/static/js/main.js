$(document).ready(function(){
  console.log("main.js loaded.");

   --- [1] Obsługa trybu ciemnego (dark-theme) ---
  let savedTheme = localStorage.getItem("theme") || "dark"; // Domyślnie ciemny
if (savedTheme === "dark") {
  $("html, body").addClass("dark-theme");
} else {
  $("html, body").removeClass("dark-theme");
}


  $("#toggle-theme").on("click", function(){
  if ($("html").hasClass("dark-theme")) {
    $("html, body").removeClass("dark-theme");
    localStorage.setItem("theme", "light");
  } else {
    $("html, body").addClass("dark-theme");
    localStorage.setItem("theme", "dark");
  }
});


  // --- [2] Lista wybranych produktów do wypożyczenia ---
  var selectedProducts = [];

  function updateSelectedProducts() {
    var $list = $("#selectedProductsList");
    $list.empty();
    selectedProducts.forEach(function(prod, index){
      $list.append(`
        <li class="list-group-item d-flex justify-content-between align-items-center">
          ${prod.name} (ID: ${prod.id})
          <button type="button" class="btn btn-sm btn-danger remove-product" data-index="${index}">&times;</button>
        </li>
      `);
    });
    // Zapisujemy jako JSON w hidden input
    $("#selectedProductsInput").val(JSON.stringify(selectedProducts));
  }

  // Dodawanie produktu z listy dostępnych
  $("#availableProductsList").on("click", ".add-product", function(){
    var $item = $(this).closest(".available-product");
    var productId = $item.data("id");
    var productName = $item.data("name");

    // Sprawdź, czy nie dodano już tego produktu
    var exists = selectedProducts.some(function(p){ return p.id == productId; });
    if (!exists) {
      selectedProducts.push({id: productId, name: productName});
      updateSelectedProducts();
    }
  });

  // Usuwanie produktu z listy wybranych
  $("#selectedProductsList").on("click", ".remove-product", function(){
    var idx = $(this).data("index");
    selectedProducts.splice(idx, 1);
    updateSelectedProducts();
  });

  // --- [3] Wyszukiwarka dostępnych produktów ---
  $("#productSearch").on("keyup", function(){
    var query = $(this).val().toLowerCase();
    $("#availableProductsList .available-product").each(function(){
      var fullName = $(this).data("name").toLowerCase();
      if (fullName.indexOf(query) !== -1) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });

  // Ewentualnie obsługa modala produktu (historii) – pobieranie AJAX-em
  $(".product-item").on("click", function(){
    var productId = $(this).data("id");
    // Przykładowy request do /product/<id>/detail/
    // Możesz tu wstawić kod otwierający inny modal ze szczegółami.
    console.log("Kliknięto produkt o ID", productId);
  });



  // Po kliknięciu w element .product-item pobieramy ID i wywołujemy AJAX
  $("#productsList").on("click", ".product-item", function(){
    var productId = $(this).data("id");

    $.ajax({
      url: "/product/" + productId + "/detail_ajax/",
      method: "GET",
      success: function(resp){
        // resp zawiera: brand, model, code, custom_name, serial_number, description, state, photo_url
        var photoPart = resp.photo_url
          ? `<img src="${resp.photo_url}" class="img-fluid mb-3" alt="Zdjęcie produktu">`
          : `<p class="text-muted">Brak zdjęcia</p>`;

        var html = `
          <div class="row">
            <div class="col-md-4">
              ${photoPart}
            </div>
            <div class="col-md-8">
              <h5>${resp.brand} ${resp.model} (${resp.code})</h5>
              <p><strong>Nazwa własna:</strong> ${resp.custom_name || '-'}</p>
              <p><strong>Numer seryjny:</strong> ${resp.serial_number || '-'}</p>
              <p><strong>Stan:</strong> ${resp.state}</p>
              <p><strong>Opis:</strong> ${resp.description || '-'}</p>
            </div>
          </div>
        `;

        $("#productDetailContent").html(html);
        $("#productDetailModal").modal("show");
      },
      error: function(){
        alert("Nie udało się pobrać danych produktu.");
      }
    });


});


});
