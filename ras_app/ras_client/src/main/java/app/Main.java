package app;

import java.io.File;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.HashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.apache.commons.lang3.ArrayUtils;

import com.google.common.net.InetAddresses;
import com.google.common.net.InternetDomainName;
import com.google.gson.Gson;

import Server.SimpleTask;
import experiment.RandomStep;
import gnu.getopt.Getopt;
import gnu.getopt.LongOpt;
import net.spy.memcached.MemcachedClient;

public class Main {
	private static Integer initPop = -1;
	private static String jedisHost = null;
	private static String[] systemQueues = null;
	private static File expFile = null;
	private static String tier1Host;

	public static void main(String[] args) {

		System.setProperty("net.spy.log.LoggerImpl", "net.spy.memcached.compat.log.SLF4JLogger");

		Main.getCliOptions(args);
		final SimpleTask[] Sys = Main.genSystem();
		Main.resetState(Sys[0]);
		Sys[0].start();
		//Main.startSim(Sys[0]);
	}

	public static void resetState(SimpleTask task) {
		MemcachedClient memcachedClient = null;
		try {
			memcachedClient = new MemcachedClient(new InetSocketAddress(Main.jedisHost, 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
		try {
			for (String e : Main.systemQueues) {
				if (e.equals("think")) {
					memcachedClient.set("think", 3600, String.valueOf(0)).get();
				} else {
					if (e.endsWith("_sw") || e.endsWith("_hw")) {
						memcachedClient.set(e, 3600, "1").get();
					} else {
						memcachedClient.set(e, 3600, "0").get();
					}
				}
			}
		} catch (InterruptedException | ExecutionException e1) {
			e1.printStackTrace();
		}
		memcachedClient.shutdown();
	}

	public static SimpleTask[] genSystem() {
		HashMap<String, Class> clientEntries = new HashMap<String, Class>();
		HashMap<String, Long> clientEntries_stimes = new HashMap<String, Long>();
		Client.setTier1Host(Main.tier1Host);
		clientEntries.put("think", Client.class);
		clientEntries_stimes.put("think", 1000l);
		final SimpleTask client = new SimpleTask(clientEntries, clientEntries_stimes, Main.initPop, "Client",
				Main.jedisHost);
		return new SimpleTask[] { client };
	}

	public static boolean validate(final String hostname) {
		return InetAddresses.isUriInetAddress(hostname) || InternetDomainName.isValid(hostname);
	}

	private static void startSim(SimpleTask client) {
		ScheduledExecutorService se = Executors.newSingleThreadScheduledExecutor();
		RandomStep simClock = new RandomStep(client);
		se.scheduleAtFixedRate(simClock, 0, 1, TimeUnit.SECONDS);
	}

	public static void getCliOptions(String[] args) {
		int c;
		LongOpt[] longopts = new LongOpt[4];
		longopts[0] = new LongOpt("initPop", LongOpt.REQUIRED_ARGUMENT, null, 0);
		longopts[1] = new LongOpt("jedisHost", LongOpt.REQUIRED_ARGUMENT, null, 1);
		longopts[2] = new LongOpt("queues", LongOpt.REQUIRED_ARGUMENT, null, 2);
		longopts[3] = new LongOpt("tier1Host", LongOpt.REQUIRED_ARGUMENT, null, 3);

		Getopt g = new Getopt("ddctrl", args, "", longopts);
		g.setOpterr(true);
		while ((c = g.getopt()) != -1) {
			switch (c) {
			case 0:
				try {
					Main.initPop = Integer.valueOf(g.getOptarg());
				} catch (NumberFormatException e) {
					System.err.println(String.format("%s is not valid, it must be 0 or 1.", g.getOptarg()));
				}
				break;
			case 1:
				try {
					if (!Main.validate(g.getOptarg())) {
						throw new Exception(String.format("%s is not a valid jedis URL", g.getOptarg()));
					}
					Main.jedisHost = String.valueOf(g.getOptarg());
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			case 2:
				try {
					Gson gson = new Gson();
					Main.systemQueues = gson.fromJson(String.valueOf(g.getOptarg()), String[].class);
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			case 3:
				try {
					Main.tier1Host = String.valueOf(g.getOptarg()); 
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			default:
				break;
			}
		}
	}
}
