#include <SModelS.h>
#include <iostream>

using namespace std;

int main( int argc, char * argv[] )
{
  /** initialise SModelS, load database */
  SModelS smodels ( "./parameters.ini" ); 
  /** run over one single file or directory */
  int ret = smodels.run ( "test.slha" );
  cout << "[run.cpp] ret=" << ret << endl;
}
