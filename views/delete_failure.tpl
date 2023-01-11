% include('header.tpl', title=name)

  <div class="alert alert-danger" role="alert">
    {{error_message}}
  </div>


<ul class="nav">
    <li class="nav-item">
        <a class="nav-link active" href="/home">Go to Image Gallery</a>
    </li>
</ul>

% include('footer.tpl')