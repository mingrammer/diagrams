jQuery(document).ready(function () {

    var example_1_btn = jQuery('#example_1_btn');
    var example_2_btn = jQuery('#example_2_btn');
    var example_3_btn = jQuery('#example_3_btn');
    var more_example_btn = jQuery('#more_example_btn');

    var diagrams_form = jQuery('#diagrams_form');

    var diagrams_data_textarea = jQuery('#diagrams_data');

    function InsertDiagramsText(text) {
        diagrams_data_textarea.val(text);
        diagrams_form.submit();
    }

    example_1_btn.click(function(){
      InsertDiagramsText(jQuery("#example_1_text").html().trim());
    });
    example_2_btn.click(function(){
      InsertDiagramsText(jQuery("#example_2_text").html().trim());
    });
    example_3_btn.click(function(){
      InsertDiagramsText(jQuery("#example_3_text").html().trim());
    });
    more_example_btn.click(function(){
      window.open("https://diagrams.mingrammer.com/docs/getting-started/examples", "_blank");
    });

});
