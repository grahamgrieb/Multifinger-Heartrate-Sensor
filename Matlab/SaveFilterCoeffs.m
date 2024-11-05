 % open your file for writing
 fid = fopen('IIR_1.csv','wt');
 % write the matrix
 if fid > 0
     fprintf(fid,'%d,%d,%d,%d,%d,%d\n',SOS');
     fclose(fid);
 end