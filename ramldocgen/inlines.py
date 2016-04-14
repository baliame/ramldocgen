highlight_inline_js = """$(document).ready(function() {
  $('.page-header pre code, .top-resource-description pre code').each(function(i, block) {
    hljs.highlightBlock(block);
  });

  $('[data-toggle]').click(function() {
    var selector = $(this).data('target') + ' pre code';
    $(selector).each(function(i, block) {
      hljs.highlightBlock(block);
    });
  });

  // open modal on hashes like #_action_get
  $(window).bind('hashchange', function(e) {
    var anchor_id = document.location.hash.substr(1); //strip #
    var element = $('#' + anchor_id);

    // do we have such element + is it a modal?  --> show it
    if (element.length && element.hasClass('modal')) {
      element.modal('show');
    }
  });

  // execute hashchange on first page load
  $(window).trigger('hashchange');
  $('a').click(function() {
    $('[data-spy="scroll"]').each(function () {
      $(this).scrollspy('refresh');
    });
  })

  // remove url fragment on modal hide
  $('.modal').on('hidden.bs.modal', function() {
    try {
      if (history && history.replaceState) {
          history.replaceState({}, '', '#');
      }
    } catch(e) {}
  });
});
"""

api_doc_inline_css = """
.hljs {
  background: transparent;
}
.glyphicon {
  line-height: 99%;
}
.parent {
  color: #999;
}
.list-group-item > .badge {
  float: none;
  margin-right: 6px;
}
.panel-title > .methods {
  float: right;
}
.badge {
  border-radius: 0;
  text-transform: uppercase;
  width: 70px;
  font-weight: normal;
  color: #f3f3f6;
  line-height: normal;
  padding-top: 4px;
}
.badge_get, .badge_information {
  background-color: #63a8e2;
}
.badge_post {
  background-color: #6cbd7d;
}
.badge_put {
  background-color: #22bac4;
}
.badge_delete {
  background-color: #d26460;
}
.badge_patch {
  background-color: #ccc444;
}
.list-group, .panel-group {
  margin-bottom: 0;
}
.panel-group .panel+.panel-white {
  margin-top: 0;
}
.panel-group .panel-white {
  border-bottom: 1px solid #F5F5F5;
  border-radius: 0;
}
.panel-white:last-child {
  border-bottom-color: white;
  -webkit-box-shadow: none;
  box-shadow: none;
}
.panel-white .panel-heading {
  background: white;
}
.tab-pane ul {
  padding-left: 2em;
}
.tab-pane h2 {
  font-size: 1.2em;
  padding-bottom: 4px;
  border-bottom: 1px solid #ddd;
}
.tab-pane h3 {
  font-size: 1.1em;
}
.tab-content {
  border-left: 1px solid #ddd;
  border-right: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
  padding: 10px;
}
#sidebar {
  margin-top: 30px;
  padding-right: 5px;
  overflow: auto;
  height: 90%;
}
.top-resource-description {
  border-bottom: 1px solid #ddd;
  background: #fcfcfc;
  padding: 15px 15px 0 15px;
  margin: -15px -15px 10px -15px;
}
.resource-description {
  border-bottom: 1px solid #fcfcfc;
  background: #fcfcfc;
  padding: 15px 15px 0 15px;
  margin: -15px -15px 10px -15px;
}
.resource-description p:last-child {
  margin: 0;
}
.list-group .badge {
  float: left;
}
.method_description {
  margin-left: 85px;
}
.method_description p:last-child {
  margin: 0;
}
.list-group-item {
  cursor: pointer;
}
.list-group-item:hover {
  background-color: #f5f5f5;
}
html {
  height: 100%;
}
pre {
  font-size: 11px;
}
ul.nav-pills.nav-stacked.subnav>li>a {
  padding-left: 35px;
  border-left: 3px solid transparent;
}
ul.nav-pills.nav-stacked>li>a {
  font-weight: normal;
  border-radius: 0px;
  padding-top: 4px;
  padding-bottom: 4px;
}
ul.nav-pills.nav-stacked.subnav>li>a {
  padding-top: 2px;
  padding-bottom: 2px;
}
ul.nav-pills.nav-stacked>li>ul.subnav {
  display: none;
}

ul.nav-pills.nav-stacked>li.active>ul.subnav {
  display: block;
}
ul.nav-pills.nav-stacked>li.active>a {
  font-weight: bold;
  border-left: 3px solid #428bca;
  background: #fff;
  color: #428bca;
}
ul.nav-pills.nav-stacked.subnav>li.active>a {
  font-weight: bold;
  border-left: 3px solid #d26460;
  background: #fff;
  color: #d26460;
}
ul.nav-pills.nav-stacked>li>a:hover {
  background-color: #eee;
}
.right-aligned {
  float: right;
  padding: 0px 15px;
}
.badge.double {
  width: 145px;
}
.authentication {
  padding: 10px 0px;
}
.authentication.top {
  padding-top: 0px;
}
"""