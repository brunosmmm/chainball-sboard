<!DOCTYPE html>
<html>
  <head>
    <title>Chainball Scoreboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <script type="application/x-javascript"> addEventListener("load", function() { setTimeout(hideURLbar, 0); }, false); function hideURLbar(){ window.scrollTo(0,1); } </script>
    <link href="/css/bootstrap.min.css" rel='stylesheet' type='text/css' />
    <link href="/css/style.css" rel='stylesheet' type='text/css' />
    <script src="/js/jquery.min.js"></script>
    <script src="/js/popper.min.js"></script>
    <script src="/js/bootstrap.min.js"></script>
    <link href="/css/all.css" rel="stylesheet"> <!--load all styles -->

    <script>$(document).ready(function(c) {
    $('.sky-close').on('click', function(c){
        $('.green-button').fadeOut('slow', function(c){
            $('.green-button').remove();
        });
    });
});
    </script>
    <script>$(document).ready(function(c) {
    $('.oran-close').on('click', function(c){
        $('.orange-button').fadeOut('slow', function(c){
            $('.orange-button').remove();
        });
    });
});
    </script>
    <script type="text/javascript" src="/js/Chart.js"></script>

    <!-- start a game -->
    <script>
      function startGame()
      {
          $("#game-status").load("/control/gbegin");
          setTimeout(function(){
              window.location.reload(true);
          });
      }

      function stopGame()
      {
          $.ajax({
              method: "GET",
              url: "/control/gend"
          });
      }

      var refreshTimer;
      function startRefreshing()
      {
          refreshTimer = setInterval(refreshScores, 3000);
      }

      function stopRefreshing()
      {
          clearInterval(refreshTimer);
      }

      function refreshScores()
      {
          $.ajax({
              method: "GET",
              url: "/status/game",
              success: function(result) {
                  if (result.status == "ok") {
                      if (result.game != "stopped") {
                          $.each(result.scores,
                                 function(key, val) {
                                     if (key != "status") {
                                         setScore(key, val, result.serving);
                                     }
                                 });
                      }
                  }
              }
          });
      }

      function setScore(player, score, serving)
      {
          if (serving != player) {
              $("#pline-"+player).removeClass("playerscoreactive");
          }
          else
          {
              $("#pline-"+player).addClass("playerscoreactive");
          }

          $("#pscore-"+player).text(score);
      }
    </script>

  </head>
  <body onload="{{'startRefreshing()' if gameData.ongoing else ''}}">
	  <!--content-starts-->
    <nav class="navbar sticky-top navbar-light bg-light">
      <a class="navbar-brand" href="#">Chainball Scoreboard</a>
    </nav>
          <div class="container">
            <div class="row">
              <div class="col-2">
                Player
              </div>
              <div class="col-2">
                Score
              </div>
              <div class="col-8">
                Events
              </div>
            </div>
            <div class="row">
              <!-- TODO put template here -->
              <div class="col-2">
                <button type="button" class="btn btn-block btn-primary">Player 1</button></div>
              <div class="col-2">
                <div class="dropdown">
                  <button type="button" class="btn btn-block btn-primary dropdown-toggle" id="scoreDropdownBtn0" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">0</button>
                  <div class="dropdown-menu" aria-labelledby="scoreDropdownBtn0">
                    <a class="dropdown-item" href="#">-10</a>
                    <a class="dropdown-item" href="#">-9</a>
                    <a class="dropdown-item" href="#">-8</a>
                    <a class="dropdown-item" href="#">-7</a>
                    <a class="dropdown-item" href="#">-6</a>
                    <a class="dropdown-item" href="#">-5</a>
                    <a class="dropdown-item" href="#">-4</a>
                    <a class="dropdown-item" href="#">-3</a>
                    <a class="dropdown-item" href="#">-2</a>
                    <a class="dropdown-item" href="#">-1</a>
                    <a class="dropdown-item" href="#">0</a>
                    <a class="dropdown-item" href="#">1</a>
                    <a class="dropdown-item" href="#">2</a>
                    <a class="dropdown-item" href="#">3</a>
                    <a class="dropdown-item" href="#">4</a>
                    <a class="dropdown-item" href="#">5</a>
                  </div>
                </div>
              </div>
              <div class="col-8">
                <div class="container">
                  <div class="row">
                    <div class="col-sm">
                      <button type="button" class="btn btn-danger btn-block">DF</button>
                    </div>
                    <div class="col-sm">
                      <button type="button" class="btn btn-danger btn-block">SM</button>
                    </div>
                    <div class="col-sm">
                      <button type="button" class="btn btn-warning btn-block">SH</button>
                    </div>
                    <div class="col-sm">
                      <button type="button" class="btn btn-warning btn-block">MS</button>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col-sm">
                      <button type="button" class="btn btn-warning btn-block">SP</button>
                    </div>
                    <div class="col-sm">
                      <button type="button" class="btn btn-secondary btn-block">DB</button>
                    </div>
                    <div class="col-sm">
                      <button type="button" class="btn btn-success btn-block">CB</button>
                    </div>
                    <div class="col-sm">
                      <button type="button" class="btn btn-success btn-block">JB</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
    </div>
      <nav class="navbar fixed-bottom navbar-dark bg-primary">
        <div class="btn-group" role="group" aria-label="Basic example">
          <button type="button" class="btn btn-secondary"><i class="fa fa-play" aria-hidden="true"></i></button>
          <button type="button" class="btn btn-secondary"><i class="fa fa-pause" aria-hidden="true"></i></button>
          <button type="button" class="btn btn-secondary"><i class="fa fa-stop" aria-hidden="true"></i></button>
        </div>
      </nav>
	  <!--content-end-->
  </body>
</html>
